/**
 * Playwright end-to-end smoke test (LIVE-only build).
 *
 * Requires the backend (API URL from frontend/.env.local) and frontend (:3000):
 *   cd backend && uvicorn app.main:app --port 8081
 *   cd frontend && npm run dev
 *
 * Bitcoin tests use the keyless mempool.space provider against the genesis
 * address; no API keys are required to run this suite.
 *
 * Run with: npx playwright test   (first run: npx playwright install chromium)
 */
import { expect, test } from "@playwright/test";

const FRONTEND = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const GENESIS_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";

test("dashboard loads with KPI cards and quick actions", async ({ page }) => {
  await page.goto(`${FRONTEND}/dashboard`);
  await expect(page.getByText("Total Investigations")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Transactions Analyzed")).toBeVisible();
  await expect(page.getByText("Executive Overview")).toBeVisible();
});

test("wallet investigation pipeline completes for a live Bitcoin wallet", async ({ page }) => {
  await page.goto(`${FRONTEND}/wallet`);
  await page.getByLabel("Wallet address").fill(GENESIS_ADDRESS);
  await page.getByRole("button", { name: "Investigate" }).click();
  // Pipeline tabs render once the bundle arrives (real mempool.space fetch)
  await expect(page.getByRole("tab", { name: /Threat Intelligence/i })).toBeVisible({ timeout: 45_000 });
  await expect(page.getByRole("tab", { name: /OSINT/i })).toBeVisible();
});

test("invalid wallet shows a friendly validation error", async ({ page }) => {
  await page.goto(`${FRONTEND}/wallet`);
  await page.getByLabel("Wallet address").fill("not-a-valid-wallet");
  await page.getByRole("button", { name: "Investigate" }).click();
  await expect(page.getByText(/Unrecognized address format/i).first()).toBeVisible({ timeout: 15_000 });
});

test("demo addresses are rejected in live-only mode", async ({ page }) => {
  await page.goto(`${FRONTEND}/wallet`);
  await page.getByLabel("Wallet address").fill("DEMO-RANSOM-0001");
  await page.getByRole("button", { name: "Investigate" }).click();
  await expect(page.getByText(/real blockchain APIs only/i).first()).toBeVisible({ timeout: 15_000 });
});

test("graph page renders the React Flow canvas", async ({ page }) => {
  await page.goto(`${FRONTEND}/graph`);
  await expect(page.locator(".react-flow").first()).toBeVisible({ timeout: 30_000 });
});

test("cases can be created from the UI", async ({ page }) => {
  await page.goto(`${FRONTEND}/investigations`);
  await page.getByRole("button", { name: "Create Case" }).first().click();
  await page.getByLabel("Title").fill(`E2E smoke test case ${Date.now()}`);
  await page.getByRole("button", { name: "Create case", exact: true }).click();
  await expect(page.getByText(/CASE-\d{4}-\d{3}/).first()).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Case overview")).toBeVisible();
});
