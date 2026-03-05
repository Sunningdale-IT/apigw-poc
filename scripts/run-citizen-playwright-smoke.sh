#!/usr/bin/env bash
set -euo pipefail

# Minimal Playwright smoke test for citizen portal login + dashboard visibility.
# Environment overrides:
#   CITIZEN_PORTAL_URL   (default: https://citizen.jim00.pd.test-rig.nl)
#   CITIZEN_TEST_ID      (default: CIT001)
#   PLAYWRIGHT_HEADLESS  (default: true)

if [[ -z "${BASH_VERSION:-}" ]]; then
  echo "Error: bash is required."
  exit 1
fi

if [[ ! -x "$(command -v node)" ]]; then
  echo "Error: node is required but was not found on PATH."
  exit 1
fi

if [[ ! -x "$(command -v npm)" ]]; then
  echo "Error: npm is required but was not found on PATH."
  exit 1
fi

readonly CITIZEN_PORTAL_URL="${CITIZEN_PORTAL_URL:-https://citizen.jim00.pd.test-rig.nl}"
readonly CITIZEN_TEST_ID="${CITIZEN_TEST_ID:-CIT001}"
readonly PLAYWRIGHT_HEADLESS="${PLAYWRIGHT_HEADLESS:-true}"
readonly TMP_ROOT="${TMPDIR:-/tmp}"
readonly WORK_DIR="$(mktemp -d "${TMP_ROOT}/citizen-playwright-smoke.XXXXXX")"

cleanup() {
  if [[ -d "${WORK_DIR}" ]]; then
    rm -rf "${WORK_DIR}"
  fi
}
trap cleanup EXIT

cat > "${WORK_DIR}/smoke.spec.js" <<'EOF'
const { test, expect } = require('@playwright/test');

const portalUrl = process.env.CITIZEN_PORTAL_URL;
const citizenId = process.env.CITIZEN_TEST_ID;

test('citizen can login and see dashboard', async ({ page }) => {
  await page.goto(portalUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');

  const loginInput = page.locator('#citizen_id');
  if ((await loginInput.count()) > 0) {
    await loginInput.fill(citizenId);
    await page.getByRole('button', { name: /Sign In/i }).click();
  }

  await expect(page.getByText(/Welcome,/i)).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole('heading', { name: /Available Services/i })).toBeVisible({ timeout: 15000 });
});
EOF

cat > "${WORK_DIR}/playwright.config.js" <<'EOF'
/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  timeout: 30000,
  use: {
    headless: process.env.PLAYWRIGHT_HEADLESS !== 'false',
    ignoreHTTPSErrors: true,
  },
};

module.exports = config;
EOF

echo "Installing Playwright test dependencies in ${WORK_DIR} ..."
(
  cd "${WORK_DIR}"
  npm init -y >/dev/null 2>&1
  npm install --silent --no-save @playwright/test
  npx playwright install chromium
)

echo "Running smoke test against ${CITIZEN_PORTAL_URL} using CitID ${CITIZEN_TEST_ID} ..."
(
  cd "${WORK_DIR}"
  export CITIZEN_PORTAL_URL CITIZEN_TEST_ID PLAYWRIGHT_HEADLESS
  npx playwright test "smoke.spec.js" --config="./playwright.config.js" --browser=chromium --reporter=line
)

echo "Smoke test completed."
