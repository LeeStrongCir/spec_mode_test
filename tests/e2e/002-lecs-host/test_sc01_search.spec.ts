import { test, expect } from "@playwright/test";

test.describe("SC-01: Search Navigation", () => {
  const BASE_URL = process.env.BASE_URL || "http://localhost:3000";

  test.beforeEach(async ({ page }) => {
    await page.goto("/console/dashboard");
    await page.waitForSelector("[data-testid='console-search-input']", {
      state: "visible",
      timeout: 10000,
    });
  });

  /**
   * TC-001: Verify search bar keyword matching and highlighting.
   * Input "LECS" → dropdown shows "LECS主机" with highlighted keyword.
   */
  test("TC-001: exact keyword LECS shows LECS主机 with highlight", async ({
    page,
  }) => {
    const searchInput = page.locator("[data-testid='console-search-input']");
    await searchInput.click();
    await searchInput.fill("LECS");

    const dropdown = page.locator(
      "[data-testid='search-results-dropdown']"
    );
    await expect(dropdown).toBeVisible({ timeout: 5000 });

    const lecsItem = dropdown.locator(
      "[data-testid='search-result-item'] >> text=LECS主机"
    );
    await expect(lecsItem).toBeVisible();

    const highlighted = lecsItem.locator("mark, .highlight, [class*='highlight']");
    await expect(highlighted.first()).toBeVisible();

    const highlightText = await highlighted.first().textContent();
    expect(highlightText).toMatch(/LECS/i);
  });

  /**
   * TC-002: Verify fuzzy search matching.
   * Input "云服" → fuzzy match finds "LECS主机".
   */
  test("TC-002: fuzzy search 云服 matches LECS主机", async ({ page }) => {
    const searchInput = page.locator("[data-testid='console-search-input']");
    await searchInput.click();
    await searchInput.fill("云服");

    const dropdown = page.locator(
      "[data-testid='search-results-dropdown']"
    );
    await expect(dropdown).toBeVisible({ timeout: 5000 });

    const lecsItem = dropdown.locator(
      "[data-testid='search-result-item'] >> text=LECS主机"
    );
    await expect(lecsItem).toBeVisible();

    const highlighted = lecsItem.locator("mark, .highlight, [class*='highlight']");
    await expect(highlighted.first()).toBeVisible();
  });

  /**
   * TC-003: Verify click on search result navigates to /console/lecs-hosts/list.
   */
  test("TC-003: click LECS主机 navigates to lecs-hosts list", async ({
    page,
  }) => {
    const searchInput = page.locator("[data-testid='console-search-input']");
    await searchInput.click();
    await searchInput.fill("LECS");

    const dropdown = page.locator(
      "[data-testid='search-results-dropdown']"
    );
    await expect(dropdown).toBeVisible({ timeout: 5000 });

    const lecsItem = dropdown.locator(
      "[data-testid='search-result-item'] >> text=LECS主机"
    );
    await lecsItem.click();

    await page.waitForURL("**/console/lecs-hosts/list", { timeout: 10000 });

    const currentUrl = page.url();
    expect(currentUrl).toContain("/console/lecs-hosts/list");

    await expect(
      page.locator("[data-testid='lecs-host-list-page'], h1, .page-title")
    ).toBeVisible({ timeout: 5000 });
  });

  /**
   * TC-003: Verify page loads without JS errors after navigation.
   */
  test("TC-003: list page loads without console errors", async ({ page }) => {
    const jsErrors: string[] = [];
    page.on("pageerror", (error) => {
      jsErrors.push(error.message);
    });

    const searchInput = page.locator("[data-testid='console-search-input']");
    await searchInput.click();
    await searchInput.fill("LECS");

    const dropdown = page.locator(
      "[data-testid='search-results-dropdown']"
    );
    await expect(dropdown).toBeVisible({ timeout: 5000 });

    const lecsItem = dropdown.locator(
      "[data-testid='search-result-item'] >> text=LECS主机"
    );
    await lecsItem.click();

    await page.waitForURL("**/console/lecs-hosts/list", { timeout: 10000 });

    await page.waitForTimeout(2000);

    expect(jsErrors).toHaveLength(0);
  });

  /**
   * Negative: Search with nonexistent term returns no results.
   */
  test("NEG-001: no-match search returns empty dropdown", async ({ page }) => {
    const searchInput = page.locator("[data-testid='console-search-input']");
    await searchInput.click();
    await searchInput.fill("xyz_nonexistent_term_999");

    await page.waitForTimeout(2000);

    const dropdown = page.locator(
      "[data-testid='search-results-dropdown']"
    );

    const isEmpty = await dropdown
      .locator("[data-testid='search-result-item']")
      .count()
      .then((c) => c === 0)
      .catch(() => true);
    expect(isEmpty).toBe(true);
  });

  /**
   * Regression: Case-insensitive search (lEcs) still matches LECS主机.
   */
  test("REG-001: case-insensitive search lEcs matches LECS主机", async ({
    page,
  }) => {
    const searchInput = page.locator("[data-testid='console-search-input']");
    await searchInput.click();
    await searchInput.fill("lEcs");

    const dropdown = page.locator(
      "[data-testid='search-results-dropdown']"
    );
    await expect(dropdown).toBeVisible({ timeout: 5000 });

    const lecsItem = dropdown.locator(
      "[data-testid='search-result-item'] >> text=LECS主机"
    );
    await expect(lecsItem).toBeVisible();
  });

  /**
   * Regression: Clear search and search again without residual cache.
   */
  test("REG-002: clear and re-search shows correct results", async ({
    page,
  }) => {
    const searchInput = page.locator("[data-testid='console-search-input']");

    // First search: LECS
    await searchInput.click();
    await searchInput.fill("LECS");
    const dropdown1 = page.locator(
      "[data-testid='search-results-dropdown']"
    );
    await expect(dropdown1).toBeVisible({ timeout: 5000 });

    // Clear and search again: 云服
    await searchInput.fill("");
    await searchInput.fill("云服");

    await expect(dropdown1).toBeVisible({ timeout: 5000 });

    const lecsItemAfter = dropdown1.locator(
      "[data-testid='search-result-item'] >> text=LECS主机"
    );
    await expect(lecsItemAfter).toBeVisible();
  });
});
