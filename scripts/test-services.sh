#!/bin/bash
# Test Good Behaviour and Dogcatcher (lost dogs) API flows.
#
# Usage: ./test-services.sh [--good-behaviour|--lost-dog|--all]
#
# Good Behaviour tests:
#   happy   - check known citizen CIT001, expect 200 with citizen data
#   unhappy - check unknown citizen ID, expect 404 with not-found message
#
# Dogcatcher tests:
#   happy   - list dogs via Kong /dogcatcher route, expect 200 with a JSON array
#   unhappy - fetch a non-existent dog ID, expect 404
#   photo   - fetch photo of first dog that has one, expect 200 image response
#
# Kong routes (discovered from Kong Admin):
#   /dogcatcher          → dogcatcher service (request-transformer injects auth)
#   /good-behaviour      → good-behaviour service (mTLS, via Kong)
#
# Environment overrides:
#   KONG_HOST     base hostname for Kong proxy, no scheme (default: kong.jim00.pd.test-rig.nl)
#   KONG_SCHEME   http or https (default: https)
#
# Local dev example:
#   KONG_HOST=localhost:8000 KONG_SCHEME=http ./scripts/test-services.sh

set -euo pipefail

KONG_SCHEME="${KONG_SCHEME:-https}"
KONG_HOST="${KONG_HOST:-kong.jim00.pd.test-rig.nl}"
KONG_BASE="${KONG_SCHEME}://${KONG_HOST}"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0

print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# run_test DESCRIPTION EXPECTED_STATUS JQ_BODY_CHECK [curl args...]
#   JQ_BODY_CHECK: jq expression that must evaluate to "true"; pass "" to skip
run_test() {
    local description="$1"
    local expected_status="$2"
    local body_check="$3"
    shift 3

    echo ""
    echo "  Test: ${description}"

    local response http_status body
    response=$(curl -sk -w '\n%{http_code}' "$@") || {
        echo -e "  ${RED}✗ FAIL${NC} — curl error"
        FAIL=$((FAIL + 1))
        return
    }

    http_status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "${http_status}" != "${expected_status}" ]]; then
        echo -e "  ${RED}✗ FAIL${NC} — expected HTTP ${expected_status}, got ${http_status}"
        printf '         Body: %.200s\n' "${body}"
        FAIL=$((FAIL + 1))
        return
    fi

    if [[ -n "${body_check}" ]]; then
        local result
        result=$(echo "${body}" | jq -r "${body_check}" 2>/dev/null || echo "false")
        if [[ "${result}" != "true" ]]; then
            echo -e "  ${RED}✗ FAIL${NC} — HTTP ${http_status} OK but body check failed: ${body_check}"
            printf '         Body: %.300s\n' "${body}"
            FAIL=$((FAIL + 1))
            return
        fi
    fi

    echo -e "  ${GREEN}✓ PASS${NC} — HTTP ${http_status}"
    PASS=$((PASS + 1))
}

# ─────────────────────────────────────────────────────────────
# Good Behaviour tests
# Reached via /good-behaviour route (mTLS upstream, strip_path=true)
# ─────────────────────────────────────────────────────────────
test_good_behaviour() {
    print_header "Good Behaviour"

    # Route: /good-behaviour (strip_path=true) → good-behaviour:5443/api/citizens
    local base="${KONG_BASE}/good-behaviour"

    # Happy: CIT001 is seeded with a clean record
    run_test \
        "Happy — known citizen CIT001 returns citizen data (200)" \
        "200" \
        '(.citizen_id == "CIT001") and (.first_name != null)' \
        "${base}/check/CIT001/"

    # Unhappy: non-existent citizen — Good Behaviour returns JSON 404 (not HTML)
    run_test \
        "Unhappy — unknown citizen ID returns JSON not-found (404)" \
        "404" \
        '.found == false' \
        "${base}/check/NOSUCHCITIZEN/"
}

# ─────────────────────────────────────────────────────────────
# Dogcatcher / lost dog tests
# Reached via /dogcatcher route; Kong injects X-Auth-Verified + X-API-Key
# ─────────────────────────────────────────────────────────────
test_lost_dog() {
    print_header "Dogcatcher — Lost Dog API"

    local base="${KONG_BASE}/dogcatcher/dogs"

    # Happy: list endpoint returns a JSON array
    run_test \
        "Happy — dog list returns JSON array (200)" \
        "200" \
        'type == "array"' \
        "${base}/"

    # Unhappy: dog ID that cannot exist
    run_test \
        "Unhappy — non-existent dog ID returns not-found (404)" \
        "404" \
        "" \
        "${base}/999999999/"

    # Photo: find first dog with a photo and fetch it through the same Kong route
    echo ""
    echo "  Test: Photo — first dog with a photo returns image/* (200)"

    local list_body dog_id
    list_body=$(curl -sk "${base}/") || {
        echo -e "  ${RED}✗ FAIL${NC} — curl error fetching dog list"
        FAIL=$((FAIL + 1))
        return
    }

    dog_id=$(echo "${list_body}" | jq -r '[.[] | select(.photo_filename != null)] | first | .id // empty')

    if [[ -z "${dog_id}" ]]; then
        echo -e "  ${CYAN}  SKIP${NC} — no dogs with photos found (populate test data first)"
        return
    fi

    local photo_url="${base}/${dog_id}/photo/"
    local content_type
    content_type=$(curl -sk -o /dev/null -w '%{content_type}' "${photo_url}")

    if [[ "${content_type}" == image/* ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} — HTTP 200, Content-Type: ${content_type}"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} — expected image/* content-type, got: '${content_type}'"
        FAIL=$((FAIL + 1))
    fi
}

# ─────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────
main() {
    if ! command -v jq &>/dev/null; then
        echo -e "${RED}Error: jq is required but not found on PATH.${NC}" >&2
        exit 1
    fi

    local mode="${1:---all}"

    echo ""
    echo -e "${CYAN}Target: ${KONG_BASE}${NC}"

    case "${mode}" in
        --good-behaviour) test_good_behaviour ;;
        --lost-dog)       test_lost_dog ;;
        --all)            test_good_behaviour; test_lost_dog ;;
        *)
            echo "Usage: $0 [--good-behaviour|--lost-dog|--all]" >&2
            exit 1
            ;;
    esac

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    local total=$((PASS + FAIL))
    if [[ ${FAIL} -eq 0 ]]; then
        echo -e "${GREEN}  All ${total} tests passed.${NC}"
    else
        echo -e "${RED}  ${FAIL} of ${total} tests failed.${NC}"
    fi
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    [[ ${FAIL} -eq 0 ]]
}

main "$@"
