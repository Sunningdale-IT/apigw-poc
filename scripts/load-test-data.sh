#!/bin/bash
#
# Load test data into the Dogcatcher application
#
# This script:
#   1. Downloads sample dog photos from Dog CEO API
#   2. Creates test dog entries via the API
#   3. Supports both local and remote deployments
#
# Usage:
#   ./scripts/load-test-data.sh [OPTIONS]
#
# Options:
#   -u, --url URL       Base URL for dogcatcher (default: http://localhost:5001)
#   -k, --api-key KEY   API key for authentication (reads from .env if not provided)
#   -n, --count N       Number of dogs to create (default: 10, max: 20)
#   -c, --cleanup       Remove all existing dogs before loading
#   -h, --help          Show this help message
#
# Examples:
#   ./scripts/load-test-data.sh                     # Use defaults from .env
#   ./scripts/load-test-data.sh -n 5                # Create 5 dogs
#   ./scripts/load-test-data.sh -k mykey -n 15      # Use specific API key
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
TEMP_DIR=""

# Default options
BASE_URL="http://localhost:5001"
API_KEY=""
DOG_COUNT=10
CLEANUP=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Dog data arrays
DOG_NAMES=(
    "Buddy" "Max" "Charlie" "Cooper" "Rocky"
    "Bear" "Duke" "Tucker" "Jack" "Buster"
    "Luna" "Bella" "Daisy" "Lucy" "Molly"
    "Sadie" "Bailey" "Maggie" "Sophie" "Chloe"
)

DOG_BREEDS=(
    "labrador" "golden retriever" "beagle" "bulldog" "poodle"
    "german shepherd" "husky" "boxer" "dachshund" "corgi"
    "rottweiler" "doberman" "border collie" "australian shepherd" "cocker spaniel"
    "shiba inu" "akita" "maltese" "pomeranian" "chihuahua"
)

# Dog CEO API breed mappings (for image downloads)
DOG_CEO_BREEDS=(
    "labrador" "retriever/golden" "beagle" "bulldog/english" "poodle"
    "germanshepherd" "husky" "boxer" "dachshund" "corgi/cardigan"
    "rottweiler" "doberman" "collie/border" "australian/shepherd" "spaniel/cocker"
    "shiba" "akita" "maltese" "pomeranian" "chihuahua"
)

DOG_COMMENTS=(
    "Very friendly, wearing a blue collar"
    "Appears well-cared for, microchip pending scan"
    "Found near the park, seems lost"
    "Nervous around strangers, responds to treats"
    "Active and playful, knows basic commands"
    "Senior dog, moves slowly but gentle"
    "Young puppy, approximately 6 months old"
    "No collar, well-groomed coat"
    "Found during thunderstorm, seeking shelter"
    "Limping slightly, vet check scheduled"
    "Loves belly rubs, good with children"
    "Barks at squirrels, otherwise quiet"
    "Was found near school playground"
    "Responds to whistle, trained dog"
    "Very hungry when found, now eating well"
    "Has distinctive markings, easy to identify"
    "Found with leash attached, no tag"
    "Appears to be a family pet, well-socialized"
    "Protective but friendly once introduced"
    "Missing fur patch on left side, healing"
)

# Location data (various coordinates around a fictional city)
LOCATIONS=(
    "40.7128:-74.0060:Near Central Park"
    "40.7580:-73.9855:Times Square area"
    "40.6892:-74.0445:Near Staten Island Ferry"
    "40.7484:-73.9857:Empire State vicinity"
    "40.7061:-73.9969:Brooklyn Bridge approach"
    "40.7282:-73.7949:Queens residential area"
    "40.8448:-73.8648:Bronx Zoo neighborhood"
    "40.7489:-73.9680:Midtown East"
    "40.7736:-73.9566:Upper East Side"
    "40.7831:-73.9712:Upper West Side"
    "40.7411:-74.0018:Chelsea Market area"
    "40.7614:-73.9776:Rockefeller Center"
    "40.7527:-73.9772:Grand Central vicinity"
    "40.7794:-73.9632:Metropolitan Museum area"
    "40.6501:-73.9496:Prospect Park"
    "40.7033:-73.9903:DUMBO neighborhood"
    "40.7193:-73.9951:Lower East Side"
    "40.7265:-74.0007:SoHo district"
    "40.7243:-73.9927:East Village"
    "40.7359:-74.0036:Greenwich Village"
)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_dog() {
    echo -e "${CYAN}[DOG]${NC} $1"
}

show_help() {
    head -30 "${BASH_SOURCE[0]}" | tail -26 | sed 's/^#//'
}

cleanup_temp() {
    if [[ -n "${TEMP_DIR}" ]] && [[ -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
    fi
}

trap cleanup_temp EXIT

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -u|--url)
                BASE_URL="${2:-}"
                shift 2
                ;;
            -k|--api-key)
                API_KEY="${2:-}"
                shift 2
                ;;
            -n|--count)
                DOG_COUNT="${2:-10}"
                if [[ "${DOG_COUNT}" -gt 20 ]]; then
                    log_warn "Maximum count is 20, using 20"
                    DOG_COUNT=20
                fi
                if [[ "${DOG_COUNT}" -lt 1 ]]; then
                    log_error "Count must be at least 1"
                    exit 1
                fi
                shift 2
                ;;
            -c|--cleanup)
                CLEANUP=true
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

# Load API key from .env if not provided
load_api_key() {
    if [[ -z "${API_KEY}" ]]; then
        if [[ -f "${ENV_FILE}" ]]; then
            # Try to get the admin key (second key in the comma-separated list)
            local keys
            keys=$(grep "^DOGCATCHER_API_KEYS=" "${ENV_FILE}" 2>/dev/null | cut -d'=' -f2 || echo "")
            if [[ -n "${keys}" ]]; then
                # Get the second key (admin key) or first if only one
                API_KEY=$(echo "${keys}" | cut -d',' -f2)
                if [[ -z "${API_KEY}" ]]; then
                    API_KEY=$(echo "${keys}" | cut -d',' -f1)
                fi
                log_info "Loaded API key from .env file"
            fi
        fi
    fi
    
    if [[ -z "${API_KEY}" ]]; then
        log_warn "No API key provided. The API might reject requests."
        log_warn "Use -k/--api-key option or set DOGCATCHER_API_KEYS in .env"
    fi
}

# Check required tools
check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install them and try again."
        exit 1
    fi
}

# Test API connectivity
test_api() {
    log_info "Testing API connectivity at ${BASE_URL}..."
    
    local http_code
    local curl_opts=("-s" "-o" "/dev/null" "-w" "%{http_code}" "--connect-timeout" "5")
    
    if [[ -n "${API_KEY}" ]]; then
        curl_opts+=("-H" "X-API-Key: ${API_KEY}")
    fi
    
    http_code=$(curl "${curl_opts[@]}" "${BASE_URL}/api/dogs/" 2>/dev/null || echo "000")
    
    case "${http_code}" in
        200)
            log_success "API is accessible"
            return 0
            ;;
        401|403)
            if [[ -z "${API_KEY}" ]]; then
                log_error "API requires authentication. Please provide an API key."
            else
                log_error "Invalid API key. HTTP status: ${http_code}"
            fi
            exit 1
            ;;
        000)
            log_error "Cannot connect to ${BASE_URL}. Is the server running?"
            exit 1
            ;;
        *)
            log_warn "API returned HTTP ${http_code}. Continuing anyway..."
            ;;
    esac
}

# Delete all existing dogs
cleanup_existing_dogs() {
    log_info "Cleaning up existing dog entries..."
    
    local curl_opts=("-s")
    if [[ -n "${API_KEY}" ]]; then
        curl_opts+=("-H" "X-API-Key: ${API_KEY}")
    fi
    
    local dogs_json
    dogs_json=$(curl "${curl_opts[@]}" "${BASE_URL}/api/dogs/")
    
    local dog_ids
    dog_ids=$(echo "${dogs_json}" | jq -r '.[].id' 2>/dev/null || echo "")
    
    if [[ -z "${dog_ids}" ]]; then
        log_info "No existing dogs to remove"
        return
    fi
    
    local count=0
    for dog_id in ${dog_ids}; do
        curl -s -X DELETE "${curl_opts[@]}" "${BASE_URL}/api/dogs/${dog_id}" > /dev/null
        ((count++))
    done
    
    log_success "Removed ${count} existing dog(s)"
}

# Download a dog photo from Dog CEO API with retries
download_dog_photo() {
    local breed_index=$1
    local photo_path=$2
    local max_retries=3
    local retry=0
    
    while [[ ${retry} -lt ${max_retries} ]]; do
        local breed="${DOG_CEO_BREEDS[${breed_index}]}"
        local image_url=""
        
        # Try specific breed first, then fallback to random
        if [[ ${retry} -eq 0 ]]; then
            image_url=$(curl -s --connect-timeout 5 "https://dog.ceo/api/breed/${breed}/images/random" 2>/dev/null | jq -r '.message' 2>/dev/null || echo "")
        fi
        
        # Fallback to random dog
        if [[ -z "${image_url}" ]] || [[ "${image_url}" == "null" ]]; then
            image_url=$(curl -s --connect-timeout 5 "https://dog.ceo/api/breeds/image/random" 2>/dev/null | jq -r '.message' 2>/dev/null || echo "")
        fi
        
        if [[ -n "${image_url}" ]] && [[ "${image_url}" != "null" ]]; then
            # Download with timeout
            if curl -s --connect-timeout 10 --max-time 30 -o "${photo_path}" "${image_url}" 2>/dev/null; then
                # Verify it's a valid image file and has content
                if [[ -f "${photo_path}" ]] && [[ -s "${photo_path}" ]]; then
                    local file_type
                    file_type=$(file -b "${photo_path}" 2>/dev/null || echo "")
                    if [[ "${file_type}" == *"image"* ]] || [[ "${file_type}" == *"JPEG"* ]] || [[ "${file_type}" == *"PNG"* ]] || [[ "${file_type}" == *"GIF"* ]]; then
                        return 0
                    fi
                fi
            fi
        fi
        
        ((retry++))
        if [[ ${retry} -lt ${max_retries} ]]; then
            sleep 1
        fi
    done
    
    return 1
}

# Create a single dog entry (photo required)
create_dog() {
    local index=$1
    
    # Get dog data
    local name="${DOG_NAMES[${index}]}"
    local breed="${DOG_BREEDS[${index}]}"
    local comment="${DOG_COMMENTS[${index}]}"
    local location="${LOCATIONS[${index}]}"
    
    # Parse location
    local latitude
    local longitude
    local location_note
    latitude=$(echo "${location}" | cut -d':' -f1)
    longitude=$(echo "${location}" | cut -d':' -f2)
    location_note=$(echo "${location}" | cut -d':' -f3)
    
    # Add some randomness to coordinates (within ~500m)
    local lat_offset
    local lon_offset
    lat_offset=$(awk "BEGIN {printf \"%.6f\", (${RANDOM} - 16383) / 3276700}")
    lon_offset=$(awk "BEGIN {printf \"%.6f\", (${RANDOM} - 16383) / 3276700}")
    latitude=$(awk "BEGIN {printf \"%.6f\", ${latitude} + ${lat_offset}}")
    longitude=$(awk "BEGIN {printf \"%.6f\", ${longitude} + ${lon_offset}}")
    
    # Full comment with location note
    local full_comment="${comment}. ${location_note}."
    
    log_dog "Creating: ${name} (${breed})"
    
    # Download photo (required)
    local photo_path="${TEMP_DIR}/${name}_${index}.jpg"
    
    if ! download_dog_photo "${index}" "${photo_path}"; then
        log_error "  Failed to download photo for ${name} after retries - skipping"
        return 1
    fi
    
    log_info "  Downloaded photo for ${name}"
    
    # Get initial dog count to verify creation
    local curl_opts=("-s")
    if [[ -n "${API_KEY}" ]]; then
        curl_opts+=("-H" "X-API-Key: ${API_KEY}")
    fi
    
    local before_count
    before_count=$(curl "${curl_opts[@]}" "${BASE_URL}/api/dogs/" 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    
    # Create the dog entry via the web form (which handles photo upload)
    # Don't follow redirects (-L not used) so we can check for 302 success
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        --connect-timeout 10 \
        --max-time 60 \
        -F "name=${name}" \
        -F "breed=${breed}" \
        -F "latitude=${latitude}" \
        -F "longitude=${longitude}" \
        -F "comments=${full_comment}" \
        -F "photo=@${photo_path}" \
        "${BASE_URL}/add_dog" 2>/dev/null || echo "000")
    
    # Check if the request succeeded (302 redirect means success for form submission)
    if [[ "${http_code}" != "200" ]] && [[ "${http_code}" != "302" ]] && [[ "${http_code}" != "303" ]]; then
        log_error "  Failed to create ${name} - HTTP ${http_code}"
        return 1
    fi
    
    # Verify the dog was actually created by checking count increased
    sleep 0.3
    local after_count
    after_count=$(curl "${curl_opts[@]}" "${BASE_URL}/api/dogs/" 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    
    if [[ "${after_count}" -le "${before_count}" ]]; then
        log_error "  Failed to verify creation of ${name} (count unchanged)"
        return 1
    fi
    
    log_success "  Created ${name} at (${latitude}, ${longitude})"
    return 0
}

# Main function
main() {
    parse_args "$@"
    check_dependencies
    load_api_key
    
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}        ${GREEN}Dogcatcher Test Data Loader${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log_info "Configuration:"
    echo "  URL:       ${BASE_URL}"
    echo "  Dog Count: ${DOG_COUNT}"
    echo "  Cleanup:   ${CLEANUP}"
    echo ""
    
    # Test API connectivity
    test_api
    
    # Create temp directory for photos
    TEMP_DIR=$(mktemp -d)
    log_info "Using temp directory: ${TEMP_DIR}"
    
    # Cleanup existing dogs if requested
    if [[ "${CLEANUP}" == true ]]; then
        cleanup_existing_dogs
    fi
    
    # Create dogs
    echo ""
    log_info "Creating ${DOG_COUNT} dog entries (photos required)..."
    echo ""
    
    local created=0
    local failed=0
    local attempts=0
    local max_data_index=20  # We have 20 entries in our data arrays
    local current_index=0
    
    # Keep trying until we create enough dogs or run out of data
    while [[ ${created} -lt ${DOG_COUNT} ]] && [[ ${current_index} -lt ${max_data_index} ]]; do
        ((attempts++))
        
        if create_dog "${current_index}"; then
            ((created++))
        else
            ((failed++))
        fi
        
        ((current_index++))
        
        # Small delay to be nice to the Dog CEO API
        sleep 0.5
    done
    
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    
    if [[ ${created} -ge ${DOG_COUNT} ]]; then
        log_success "Test data loading complete!"
    else
        log_warn "Could only create ${created} of ${DOG_COUNT} requested dogs"
    fi
    
    echo ""
    echo "  Requested: ${DOG_COUNT} dogs"
    echo "  Created:   ${created} dogs"
    if [[ ${failed} -gt 0 ]]; then
        echo "  Failed:    ${failed} dogs"
    fi
    echo ""
    echo "  View dogs at: ${BASE_URL}/browse"
    echo "  API docs at:  ${BASE_URL}/api/docs"
    echo ""
}

main "$@"
