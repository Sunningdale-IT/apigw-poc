#!/bin/bash
#
# Create Azure VM for Dogcatcher Application
#
# This script creates an Ubuntu VM on Azure with:
#   - 2 vCPUs, 4GB RAM
#   - Docker and Docker Compose installed
#   - Ports 22 (SSH) and 443 (HTTPS) open
#   - Optional: ports 80, 8080 for HTTP access
#
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - SSH key pair (~/.ssh/id_rsa.pub or specify with --ssh-key)
#
# Usage:
#   ./azure-create-vm.sh [OPTIONS]
#
# Options:
#   -n, --name            VM name (default: dogcatcher-vm)
#   -g, --resource-group  Resource group name (default: dogcatcher-rg)
#   -l, --location        Azure region (default: uksouth)
#   -s, --size            VM size (default: Standard_B2s)
#   --ssh-key             Path to SSH public key (default: ~/.ssh/id_rsa.pub)
#   --admin-user          Admin username (default: azureuser)
#   --open-http           Also open ports 8080 and 8443
#   --install-app         Clone and start Dogcatcher app after VM creation
#   --auto-delete TIME    Schedule daily deletion (default: 19:00, format HH:MM)
#   --no-auto-delete      Disable auto-deletion scheduling
#   --dry-run             Show commands without executing
#   -h, --help            Show this help message
#
# Examples:
#   ./azure-create-vm.sh
#   ./azure-create-vm.sh --name my-vm --location westeurope
#   ./azure-create-vm.sh --open-http --install-app
#

set -euo pipefail

# Default values
VM_NAME="dogcatcher-vm"
RESOURCE_GROUP="dogcatcher-rg"
LOCATION="uksouth"
VM_SIZE="Standard_B2s"  # 2 vCPU, 4GB RAM
SSH_KEY_PATH="${HOME}/.ssh/id_rsa.pub"
ADMIN_USER="azureuser"
OPEN_HTTP=false
INSTALL_APP=false
AUTO_DELETE=true
AUTO_DELETE_TIME="19:00"
DRY_RUN=false

# Ubuntu 22.04 LTS image
IMAGE="Ubuntu2204"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

show_help() {
    head -36 "${BASH_SOURCE[0]}" | tail -32 | sed 's/^#//'
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--name)
                VM_NAME="$2"
                shift 2
                ;;
            -g|--resource-group)
                RESOURCE_GROUP="$2"
                shift 2
                ;;
            -l|--location)
                LOCATION="$2"
                shift 2
                ;;
            -s|--size)
                VM_SIZE="$2"
                shift 2
                ;;
            --ssh-key)
                SSH_KEY_PATH="$2"
                shift 2
                ;;
            --admin-user)
                ADMIN_USER="$2"
                shift 2
                ;;
            --open-http)
                OPEN_HTTP=true
                shift
                ;;
            --install-app)
                INSTALL_APP=true
                shift
                ;;
            --auto-delete)
                AUTO_DELETE=true
                if [[ -n "${2:-}" ]] && [[ ! "$2" =~ ^-- ]]; then
                    AUTO_DELETE_TIME="$2"
                    shift
                fi
                shift
                ;;
            --no-auto-delete)
                AUTO_DELETE=false
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Execute or print command based on dry-run mode
run_cmd() {
    if [[ "${DRY_RUN}" == true ]]; then
        echo "  [DRY-RUN] $*"
    else
        "$@"
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed"
        log_error "Install with: brew install azure-cli (macOS) or see https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure CLI"
        log_error "Run: az login"
        exit 1
    fi
    
    # Check SSH key
    if [[ ! -f "${SSH_KEY_PATH}" ]]; then
        log_error "SSH public key not found: ${SSH_KEY_PATH}"
        log_error "Generate with: ssh-keygen -t rsa -b 4096"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
    
    # Show current subscription
    local subscription
    subscription=$(az account show --query name -o tsv)
    log_info "Using Azure subscription: ${subscription}"
}

create_resource_group() {
    log_info "Creating resource group: ${RESOURCE_GROUP}..."
    
    # Check if exists
    if az group show --name "${RESOURCE_GROUP}" &> /dev/null; then
        log_warn "Resource group ${RESOURCE_GROUP} already exists"
    else
        run_cmd az group create \
            --name "${RESOURCE_GROUP}" \
            --location "${LOCATION}" \
            --output none
        log_success "Resource group created"
    fi
}

create_network_security_group() {
    local nsg_name="${VM_NAME}-nsg"
    
    log_info "Creating network security group: ${nsg_name}..."
    
    # Create NSG
    run_cmd az network nsg create \
        --resource-group "${RESOURCE_GROUP}" \
        --name "${nsg_name}" \
        --output none
    
    # Allow SSH (port 22)
    log_info "Opening port 22 (SSH)..."
    run_cmd az network nsg rule create \
        --resource-group "${RESOURCE_GROUP}" \
        --nsg-name "${nsg_name}" \
        --name "Allow-SSH" \
        --priority 100 \
        --destination-port-ranges 22 \
        --access Allow \
        --protocol Tcp \
        --output none
    
    # Allow HTTPS (port 443)
    log_info "Opening port 443 (HTTPS)..."
    run_cmd az network nsg rule create \
        --resource-group "${RESOURCE_GROUP}" \
        --nsg-name "${nsg_name}" \
        --name "Allow-HTTPS" \
        --priority 110 \
        --destination-port-ranges 443 \
        --access Allow \
        --protocol Tcp \
        --output none
    
    # Allow HTTP (port 80) for Let's Encrypt and redirects
    log_info "Opening port 80 (HTTP - for Let's Encrypt)..."
    run_cmd az network nsg rule create \
        --resource-group "${RESOURCE_GROUP}" \
        --nsg-name "${nsg_name}" \
        --name "Allow-HTTP" \
        --priority 120 \
        --destination-port-ranges 80 \
        --access Allow \
        --protocol Tcp \
        --output none
    
    # Optionally allow additional HTTP ports
    if [[ "${OPEN_HTTP}" == true ]]; then
        log_info "Opening port 8080 (HTTP-Alt)..."
        run_cmd az network nsg rule create \
            --resource-group "${RESOURCE_GROUP}" \
            --nsg-name "${nsg_name}" \
            --name "Allow-HTTP-8080" \
            --priority 130 \
            --destination-port-ranges 8080 \
            --access Allow \
            --protocol Tcp \
            --output none
        
        log_info "Opening port 8443 (mTLS)..."
        run_cmd az network nsg rule create \
            --resource-group "${RESOURCE_GROUP}" \
            --nsg-name "${nsg_name}" \
            --name "Allow-mTLS" \
            --priority 140 \
            --destination-port-ranges 8443 \
            --access Allow \
            --protocol Tcp \
            --output none
    fi
    
    log_success "Network security group configured"
}

create_vm() {
    log_info "Creating VM: ${VM_NAME}..."
    log_info "  Size: ${VM_SIZE} (2 vCPU, 4GB RAM)"
    log_info "  Image: ${IMAGE}"
    log_info "  Location: ${LOCATION}"
    
    # Cloud-init script to install Docker
    local cloud_init_file
    cloud_init_file=$(mktemp)
    
    cat > "${cloud_init_file}" << 'CLOUD_INIT'
#cloud-config
package_update: true
package_upgrade: true

packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - lsb-release
  - git
  - jq

runcmd:
  # Install Docker
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  - echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  - apt-get update
  - apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  
  # Add azureuser to docker group
  - usermod -aG docker azureuser
  
  # Enable and start Docker
  - systemctl enable docker
  - systemctl start docker
  
  # Create app directory
  - mkdir -p /opt/dogcatcher
  - chown azureuser:azureuser /opt/dogcatcher
  
  # Log completion
  - echo "Docker installation complete" > /var/log/cloud-init-docker.log
  - docker --version >> /var/log/cloud-init-docker.log
  - docker compose version >> /var/log/cloud-init-docker.log

final_message: "Dogcatcher VM setup complete after $UPTIME seconds"
CLOUD_INIT

    # Create the VM
    run_cmd az vm create \
        --resource-group "${RESOURCE_GROUP}" \
        --name "${VM_NAME}" \
        --image "${IMAGE}" \
        --size "${VM_SIZE}" \
        --admin-username "${ADMIN_USER}" \
        --ssh-key-values "${SSH_KEY_PATH}" \
        --nsg "${VM_NAME}-nsg" \
        --public-ip-sku Standard \
        --custom-data "${cloud_init_file}" \
        --output none
    
    rm -f "${cloud_init_file}"
    
    log_success "VM created successfully"
}

get_vm_ip() {
    local public_ip
    
    if [[ "${DRY_RUN}" == true ]]; then
        public_ip="<DRY-RUN-IP>"
    else
        public_ip=$(az vm show \
            --resource-group "${RESOURCE_GROUP}" \
            --name "${VM_NAME}" \
            --show-details \
            --query publicIps \
            -o tsv)
    fi
    
    echo "${public_ip}"
}

schedule_auto_delete() {
    local automation_account="${VM_NAME}-automation"
    local runbook_name="delete-${RESOURCE_GROUP}"
    local schedule_name="daily-delete-${RESOURCE_GROUP}"
    
    log_info "Setting up auto-deletion at ${AUTO_DELETE_TIME} daily..."
    
    # Create Automation Account
    log_info "Creating Azure Automation Account..."
    run_cmd az automation account create \
        --name "${automation_account}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --output none
    
    # Create the runbook script
    local runbook_script
    runbook_script=$(mktemp)
    
    cat > "${runbook_script}" << RUNBOOK_EOF
#!/usr/bin/env pwsh
# PowerShell runbook to delete resource group
\$ErrorActionPreference = "Stop"

Write-Output "Starting scheduled deletion of resource group: ${RESOURCE_GROUP}"
Write-Output "Time: \$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

try {
    # Connect using managed identity
    Connect-AzAccount -Identity
    
    # Check if resource group exists
    \$rg = Get-AzResourceGroup -Name "${RESOURCE_GROUP}" -ErrorAction SilentlyContinue
    
    if (\$rg) {
        Write-Output "Deleting resource group: ${RESOURCE_GROUP}"
        Remove-AzResourceGroup -Name "${RESOURCE_GROUP}" -Force
        Write-Output "Resource group deleted successfully"
    } else {
        Write-Output "Resource group ${RESOURCE_GROUP} not found - may already be deleted"
    }
} catch {
    Write-Error "Failed to delete resource group: \$_"
    throw
}
RUNBOOK_EOF

    # Create the runbook
    log_info "Creating deletion runbook..."
    run_cmd az automation runbook create \
        --automation-account-name "${automation_account}" \
        --resource-group "${RESOURCE_GROUP}" \
        --name "${runbook_name}" \
        --type PowerShell \
        --output none
    
    # Upload runbook content
    if [[ "${DRY_RUN}" != true ]]; then
        az automation runbook replace-content \
            --automation-account-name "${automation_account}" \
            --resource-group "${RESOURCE_GROUP}" \
            --name "${runbook_name}" \
            --content @"${runbook_script}" \
            --output none
        
        # Publish the runbook
        az automation runbook publish \
            --automation-account-name "${automation_account}" \
            --resource-group "${RESOURCE_GROUP}" \
            --name "${runbook_name}" \
            --output none
    fi
    
    rm -f "${runbook_script}"
    
    # Enable system-assigned managed identity for automation account
    log_info "Enabling managed identity..."
    run_cmd az automation account identity assign \
        --automation-account-name "${automation_account}" \
        --resource-group "${RESOURCE_GROUP}" \
        --output none
    
    # Get subscription ID
    local subscription_id
    if [[ "${DRY_RUN}" == true ]]; then
        subscription_id="<SUBSCRIPTION_ID>"
    else
        subscription_id=$(az account show --query id -o tsv)
    fi
    
    # Get the automation account's principal ID
    local principal_id
    if [[ "${DRY_RUN}" == true ]]; then
        principal_id="<PRINCIPAL_ID>"
    else
        principal_id=$(az automation account show \
            --name "${automation_account}" \
            --resource-group "${RESOURCE_GROUP}" \
            --query identity.principalId -o tsv)
        
        # Wait for identity propagation
        sleep 30
    fi
    
    # Assign Contributor role to the managed identity for the resource group
    log_info "Assigning deletion permissions..."
    run_cmd az role assignment create \
        --assignee "${principal_id}" \
        --role "Contributor" \
        --scope "/subscriptions/${subscription_id}/resourceGroups/${RESOURCE_GROUP}" \
        --output none 2>/dev/null || true
    
    # Parse time for schedule
    local hour minute
    hour=$(echo "${AUTO_DELETE_TIME}" | cut -d: -f1)
    minute=$(echo "${AUTO_DELETE_TIME}" | cut -d: -f2)
    
    # Calculate next run time (today or tomorrow at specified time)
    local start_time
    if [[ "${DRY_RUN}" == true ]]; then
        start_time="<START_TIME>"
    else
        # Get current UTC time and create schedule start time
        local now_utc
        now_utc=$(date -u +%H%M)
        local schedule_utc="${hour}${minute}"
        
        if [[ "${now_utc}" -ge "${schedule_utc}" ]]; then
            # Schedule for tomorrow
            start_time=$(date -u -v+1d "+%Y-%m-%dT${AUTO_DELETE_TIME}:00Z" 2>/dev/null || \
                        date -u -d "+1 day" "+%Y-%m-%dT${AUTO_DELETE_TIME}:00Z")
        else
            # Schedule for today
            start_time=$(date -u "+%Y-%m-%dT${AUTO_DELETE_TIME}:00Z")
        fi
    fi
    
    # Create schedule
    log_info "Creating daily schedule at ${AUTO_DELETE_TIME} UTC..."
    run_cmd az automation schedule create \
        --automation-account-name "${automation_account}" \
        --resource-group "${RESOURCE_GROUP}" \
        --name "${schedule_name}" \
        --frequency Day \
        --interval 1 \
        --start-time "${start_time}" \
        --output none
    
    # Link schedule to runbook
    log_info "Linking schedule to runbook..."
    if [[ "${DRY_RUN}" != true ]]; then
        az automation job-schedule create \
            --automation-account-name "${automation_account}" \
            --resource-group "${RESOURCE_GROUP}" \
            --runbook-name "${runbook_name}" \
            --schedule-name "${schedule_name}" \
            --output none 2>/dev/null || true
    fi
    
    log_success "Auto-deletion scheduled for ${AUTO_DELETE_TIME} UTC daily"
    log_warn "Note: The resource group (including this automation) will be deleted!"
}

wait_for_cloud_init() {
    local public_ip="$1"
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for cloud-init to complete (Docker installation)..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY-RUN] Would wait for cloud-init completion"
        return
    fi
    
    while [[ ${attempt} -le ${max_attempts} ]]; do
        log_info "Checking cloud-init status (attempt ${attempt}/${max_attempts})..."
        
        # Check if cloud-init is complete
        if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
            "${ADMIN_USER}@${public_ip}" \
            "cloud-init status --wait" 2>/dev/null | grep -q "done"; then
            log_success "Cloud-init completed"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_warn "Cloud-init may not be complete. Check VM logs."
}

install_dogcatcher_app() {
    local public_ip="$1"
    
    log_info "Installing Dogcatcher application..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY-RUN] Would install Dogcatcher app"
        return
    fi
    
    # SSH commands to clone and start the app
    # Pass public_ip as environment variable to the remote script
    ssh -o StrictHostKeyChecking=no "${ADMIN_USER}@${public_ip}" "PUBLIC_IP='${public_ip}' bash -s" << 'REMOTE_SCRIPT'
set -e

cd /opt/dogcatcher

# Clone the repository (replace with your actual repo)
if [ ! -d "apigw-poc" ]; then
    git clone https://github.com/Sunningdale-IT/apigw-poc.git
fi

cd apigw-poc

# Generate random secrets
DOGCATCHER_SECRET=$(openssl rand -hex 32)
CITIZEN_SECRET=$(openssl rand -hex 32)

# Create environment file for production
cat > .env << EOF
# Dogcatcher API Configuration
DOGCATCHER_SECRET_KEY=${DOGCATCHER_SECRET}
DOGCATCHER_API_KEYS=demo-api-key-12345
API_KEY_REQUIRED=true
FLASK_DEBUG=false

# Proxy Configuration
PROXY_MODE=prod
ENABLE_HTTPS=true
ENABLE_MTLS=false
DOMAIN=${PUBLIC_IP}

# Citizen App Configuration
CITIZEN_SECRET_KEY=${CITIZEN_SECRET}
EOF

# Create directories for certificates
mkdir -p certs/ssl certs/mtls

# Create self-signed certificate for initial HTTPS
# (Replace with Let's Encrypt using setup-letsencrypt.sh for production)
if [ ! -f certs/ssl/server.crt ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout certs/ssl/server.key \
        -out certs/ssl/server.crt \
        -subj "/CN=${PUBLIC_IP}/O=Dogcatcher/C=GB"
    echo "Self-signed certificate created for ${PUBLIC_IP}"
fi

# Create dummy CA cert for mTLS config (required by nginx.conf)
if [ ! -f certs/ssl/ca.crt ]; then
    cp certs/ssl/server.crt certs/ssl/ca.crt
    echo "Dummy CA cert created (replace for actual mTLS)"
fi

# Start the application with Azure production overrides
docker compose -f docker-compose.yml -f docker-compose.azure.yml up -d

# Wait for services to start
sleep 15

# Check status
docker compose -f docker-compose.yml -f docker-compose.azure.yml ps

echo ""
echo "Application is now accessible at:"
echo "  https://${PUBLIC_IP}/"
echo "  https://${PUBLIC_IP}/api/docs"
echo ""
echo "Note: Browser will show certificate warning (self-signed)."
echo "Run setup-letsencrypt.sh with a domain for trusted certs."
REMOTE_SCRIPT
    
    log_success "Dogcatcher application installed"
}

print_summary() {
    local public_ip="$1"
    
    echo ""
    echo "=============================================="
    echo "  Azure VM Created Successfully"
    echo "=============================================="
    echo ""
    echo "  VM Details:"
    echo "    Name: ${VM_NAME}"
    echo "    Resource Group: ${RESOURCE_GROUP}"
    echo "    Location: ${LOCATION}"
    echo "    Size: ${VM_SIZE} (2 vCPU, 4GB RAM)"
    echo "    Public IP: ${public_ip}"
    echo ""
    echo "  Open Ports:"
    echo "    22  (SSH)"
    echo "    80  (HTTP - Let's Encrypt / redirect)"
    echo "    443 (HTTPS - main access)"
    if [[ "${OPEN_HTTP}" == true ]]; then
        echo "    8080 (HTTP-Alt)"
        echo "    8443 (mTLS)"
    fi
    echo ""
    echo "  SSH Access:"
    echo "    ssh ${ADMIN_USER}@${public_ip}"
    echo ""
    echo "  Docker Status (after cloud-init completes):"
    echo "    ssh ${ADMIN_USER}@${public_ip} 'docker --version'"
    echo ""
    if [[ "${INSTALL_APP}" == true ]]; then
        echo "  Application URLs (HTTPS on port 443):"
        echo "    https://${public_ip}/           (Web UI)"
        echo "    https://${public_ip}/api/docs   (Swagger API)"
        echo "    https://${public_ip}/plain/dogs/ (Plain API)"
        echo ""
        echo "  Note: Browser will warn about self-signed certificate."
        echo "  For trusted certs, configure DNS and run setup-letsencrypt.sh"
        echo ""
    else
        echo "  Deploy Dogcatcher:"
        echo "    1. SSH to the VM"
        echo "    2. git clone <your-repo> /opt/dogcatcher/apigw-poc"
        echo "    3. cd /opt/dogcatcher/apigw-poc"
        echo "    4. docker compose -f docker-compose.yml -f docker-compose.azure.yml up -d"
        echo ""
        echo "  The app will be accessible at https://${public_ip}/"
        echo ""
    fi
    if [[ "${AUTO_DELETE}" == true ]]; then
        echo "  Auto-Deletion:"
        echo "    Scheduled: Daily at ${AUTO_DELETE_TIME} UTC"
        echo "    WARNING: Resource group will be deleted automatically!"
        echo ""
    fi
    echo "  DNS Setup (manual):"
    echo "    Create an A record pointing to: ${public_ip}"
    echo "    Then run: ./scripts/setup-letsencrypt.sh --domain your.domain.com"
    echo ""
    echo "  Manual Cleanup:"
    echo "    az group delete --name ${RESOURCE_GROUP} --yes --no-wait"
    echo ""
    echo "=============================================="
}

main() {
    parse_args "$@"
    
    echo ""
    log_info "Azure VM Creation for Dogcatcher"
    echo ""
    log_info "Configuration:"
    log_info "  VM Name: ${VM_NAME}"
    log_info "  Resource Group: ${RESOURCE_GROUP}"
    log_info "  Location: ${LOCATION}"
    log_info "  Size: ${VM_SIZE}"
    log_info "  SSH Key: ${SSH_KEY_PATH}"
    log_info "  Open HTTP Ports: ${OPEN_HTTP}"
    log_info "  Install App: ${INSTALL_APP}"
    log_info "  Auto Delete: ${AUTO_DELETE} (at ${AUTO_DELETE_TIME} UTC)"
    log_info "  Dry Run: ${DRY_RUN}"
    echo ""
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_warn "DRY RUN MODE - Commands will be printed but not executed"
        echo ""
    fi
    
    check_prerequisites
    create_resource_group
    create_network_security_group
    create_vm
    
    local public_ip
    public_ip=$(get_vm_ip)
    
    # Schedule auto-deletion if enabled
    if [[ "${AUTO_DELETE}" == true ]]; then
        schedule_auto_delete
    fi
    
    if [[ "${INSTALL_APP}" == true ]] && [[ "${DRY_RUN}" == false ]]; then
        wait_for_cloud_init "${public_ip}"
        install_dogcatcher_app "${public_ip}"
    fi
    
    print_summary "${public_ip}"
}

main "$@"
