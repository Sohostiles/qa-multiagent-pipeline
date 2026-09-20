# QA Automated Test Report

## Summary
Automated QA testing was performed against https://www.saucedemo.com using the `problem_user` role. The run identified 62 total findings across inventory, cart, checkout, and product detail pages. The most severe issues impact checkout form progression, add-to-cart behavior, invalid navigation to 404 pages, incorrect product imagery, and broken item-not-found handling. Several accessibility and UX defects were also observed, particularly around sidebar navigation, ARIA relationships, menu controls, and checkout validation feedback.

## Test Details
- Target Application: https://www.saucedemo.com
- User Role Tested: problem_user
- Pages Analysed:
  - https://www.saucedemo.com/inventory.html
  - https://www.saucedemo.com/cart.html
  - https://www.saucedemo.com/checkout-step-one.html
  - https://www.saucedemo.com/inventory-item.html?id=1
  - https://www.saucedemo.com/inventory-item.html?id=2
  - https://www.saucedemo.com/inventory-item.html?id=3
  - https://www.saucedemo.com/inventory-item.html?id=4
  - https://www.saucedemo.com/inventory-item.html?id=5
  - https://www.saucedemo.com/inventory-item.html?id=6
- Total Issues Found: 62
- Critical: 13 | Major: 25 | Minor: 24

## Critical & Major Findings

### [CRITICAL] Checkout Last Name Input Does Not Update Correctly
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** After the intended action of filling the Last Name field with `Doe`, the form still visually shows the Last Name field empty and highlighted as invalid, with the error message `Error: Last Name is required.` The value appears in the top input instead, suggesting incorrect input targeting or broken state binding.
- **Recommended Fix:** Verify the field binding and input targeting logic for the Last Name input. Ensure entered values are rendered in the correct field and that validation state is recalculated immediately after input.

### [CRITICAL] Last Name Validation Error Persists After Valid Input
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** After entering `Doe` for the Last Name field, the form continues to display `Error: Last Name is required`, and the Last Name field remains visually marked as invalid.
- **Recommended Fix:** Revalidate the Last Name field on input or blur events and clear the associated error state once a non-empty valid value is entered.

### [CRITICAL] Entered Last Name Appears in Wrong Input Row
- **Type:** visual
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The entered value `Doe` appears in the top input row while the visible Last Name row still shows the placeholder/label `Last Name`. This makes it appear that user input was placed in the wrong field or that the UI state failed to update correctly.
- **Recommended Fix:** Verify DOM/input mapping for checkout fields and confirm each value is displayed in the correct input element. Add regression coverage for field-specific data entry.

### [CRITICAL] Invalid Price Displayed for Item-Not-Found State
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The item-not-found state still displays a nonsensical price value, `$√-1`, which appears to be placeholder, debug, or invalid calculation output rather than a valid user-facing price.
- **Recommended Fix:** Hide pricing information when an item cannot be found, or replace it with a clear message such as `Price unavailable`.

### [CRITICAL] Cart Page About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/cart.html
- **Description:** The sidebar `About` navigation link points directly to a 404 error URL. Selecting it takes users to an error page instead of the intended About destination.
- **Recommended Fix:** Update the `About` link href to a valid About or Sauce Labs informational page and verify the destination returns a successful HTTP response.

### [CRITICAL] Checkout Page About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The sidebar `About` menu link points directly to a 404 error URL, causing users to be routed to an error page rather than a valid About/Sauce Labs page.
- **Recommended Fix:** Replace the href with the correct About destination or remove/disable the menu item until a valid route is available.

### [CRITICAL] Product Detail Page ID 2 About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=2
- **Description:** The sidebar `About` menu item links directly to a 404 error URL. Users selecting the link are taken to an error page instead of a valid About page.
- **Recommended Fix:** Update the `About` href to a valid destination and include this check in navigation regression tests.

### [CRITICAL] Product Detail Page ID 3 About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=3
- **Description:** The sidebar `About` menu item points directly to a 404 error URL, resulting in broken navigation for users.
- **Recommended Fix:** Correct the URL target or remove the link if no About page exists.

### [CRITICAL] Product Detail Page ID 4 About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=4
- **Description:** The sidebar `About` navigation link points directly to a 404 error URL, so selecting it takes the user to an error page.
- **Recommended Fix:** Update the link to a valid About page and validate all sidebar links across product detail pages.

### [CRITICAL] Product Detail Page ID 5 About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=5
- **Description:** The sidebar `About` menu item points directly to a 404 error URL, preventing successful navigation to an About page.
- **Recommended Fix:** Replace the invalid URL with the correct About page route or disable the menu item until available.

### [CRITICAL] Sauce Labs Onesie Add-to-Cart Action Does Not Update Cart
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Clicking the Sauce Labs Onesie add-to-cart button did not produce the expected cart state change. The item should be added, the cart badge should increment, and the item button should change from `Add to cart` to `Remove`.
- **Recommended Fix:** Ensure the handler for `data-test='add-to-cart-sauce-labs-onesie'` updates cart state, renders the cart badge count, and swaps the item button to the corresponding Remove state.

### [CRITICAL] Completed Checkout Form Does Not Proceed to Overview
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Clicking `[data-test='continue']` after completing checkout information produced no page change, although the user should proceed to the checkout overview step.
- **Recommended Fix:** Verify the Continue button click handler, checkout form validation, and routing logic. Ensure valid form submission navigates to the checkout overview page.

### [CRITICAL] Checkout Continue Button Remains Non-Functional on Completed Form
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** A repeated attempt to submit completed checkout information using `[data-test='continue']` produced no change in the page, preventing users from progressing in the purchase flow.
- **Recommended Fix:** Add automated regression coverage for completed checkout submission and confirm the Continue action triggers validation and route transition correctly.

### [MAJOR] Product Cards Display Incorrect Duplicate Dog Image
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** All six product cards display the same unrelated dog/tennis-ball image instead of distinct product images matching listed products such as backpack, bike light, t-shirt, jacket, and onesie.
- **Recommended Fix:** Verify image source mapping for each inventory item and load the correct product-specific image assets for every product card.

### [MAJOR] Product Grid Uses Repeated Pug/Dog Placeholder Image
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** All product cards display the same pug/dog image, including Backpack, Bike Light, T-Shirt, Jacket, and Onesie. The duplicated images do not correspond to the product names and may mislead users.
- **Recommended Fix:** Ensure each inventory item is mapped to its correct image asset and remove any incorrect fallback/placeholder logic for valid products.

### [MAJOR] First Name Field Shows Required Error Despite Valid Value
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The First Name field contains `John`, but it is still shown as invalid with a red underline/error icon, and the error banner says `Error: First Name is required.`
- **Recommended Fix:** Clear the First Name validation error as soon as a valid value is entered. If another field is invalid, display the correct remaining error instead.

### [MAJOR] First Name Error Styling Conflicts with Last Name Validation Message
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The First Name field contains the valid value `John` but is still styled as an error with a red underline and icon, while the visible validation message states that Last Name is required.
- **Recommended Fix:** Remove the error state from First Name once valid input exists. Only fields failing current validation should be highlighted.

### [MAJOR] Postal Code Field Highlighted Without Matching Error Message
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The Zip/Postal Code field is shown in an error state with a red underline and error icon, even though the visible validation message only reports `Error: Last Name is required.`
- **Recommended Fix:** Apply error styling only to the field associated with the active validation error or display a specific message for each highlighted field.

### [MAJOR] Filled First Name Field Remains in Error State
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The filled First Name field still appears in an error state with a red underline and error icon, even though it contains `Doe` and the visible error message only says `Last Name is required`.
- **Recommended Fix:** Clear error styling and icons from fields as soon as they contain valid input. Keep only the actual invalid field marked as erroneous.

### [MAJOR] Valid Postal Code Field Still Marked Invalid
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The Postal Code field contains `12345` but still shows a red underline and red error icon, while the error banner only reports that Last Name is required.
- **Recommended Fix:** Update validation state after input changes so Postal Code error styling is removed once a valid value is entered.

### [MAJOR] First Name Jane Marked Required Despite Value Present
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The First Name field visibly contains `Jane`, but it remains marked with a red error state and the error banner says `Error: First Name is required.`
- **Recommended Fix:** Revalidate First Name after entry and clear the first-name error message when the field has a non-empty value.

### [MAJOR] Error Styling Applied to Multiple Valid Checkout Fields
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Validation state is applied to more fields than the displayed error explains. First Name contains `Jane` but still has error styling, and Zip/Postal Code is also highlighted while the active message only references Last Name.
- **Recommended Fix:** Apply error styling only to invalid fields or show combined field-specific messages for every field marked invalid.

### [MAJOR] All Checkout Fields Show Error State Despite Partial Valid Input
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** All three checkout fields show red error underlines and icons, even though the visible validation message only says `Last Name is required` and First Name and Postal Code contain values.
- **Recommended Fix:** Align field styling with actual validation results and avoid marking valid fields as erroneous.

### [MAJOR] Bolt T-Shirt Product Image Does Not Match Description
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** The product is labeled and described as a `Sauce Labs Bolt T-Shirt` with a red bolt, but the visible product image appears to show a plain dark T-shirt with no visible red bolt graphic.
- **Recommended Fix:** Verify the correct product image asset is used and ensure the red bolt graphic is visible in the displayed image.

### [MAJOR] Red T-Shirt Product Image Appears to Show Sweatshirt
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory-item.html?id=3
- **Description:** The product image does not match the product title and description. The item is labeled as a red T-shirt, but the image shows a long-sleeve sweatshirt/sweater.
- **Recommended Fix:** Use the correct red T-shirt image or update the title and description if the sweatshirt image is intentional.

### [MAJOR] Add-to-Cart Button Displayed for Item-Not-Found Page
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** An `Add to cart` button is displayed even though the page says `ITEM NOT FOUND`, creating an invalid and confusing state.
- **Recommended Fix:** Remove or disable add-to-cart functionality when the item is not found. Provide only relevant recovery actions such as `Back to products`.

### [MAJOR] Inventory Page About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The sidebar `About` navigation link points directly to `https://saucelabs.com/error/404`, so activating it takes users to an error page instead of a valid About page.
- **Recommended Fix:** Update the href to a valid About page URL or remove/disable the link until a valid destination exists.

### [MAJOR] Checkout Sidebar Controls Use Invalid Anchor/Button Pattern
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Several sidebar controls are anchors with `href="#"` and `role="button"` rather than native buttons or meaningful links. Without JavaScript event handling, they navigate only to the page fragment and do not have a valid destination.
- **Recommended Fix:** Use native `<button>` elements for actions or provide meaningful href values for navigation links. Ensure keyboard and assistive technology behavior matches the control type.

### [MAJOR] Product Detail Page ID 1 About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** The `About` menu item points to a 404 error URL, so activating it navigates users to an error page instead of an About page.
- **Recommended Fix:** Update the href to a valid About page URL or remove/disable the link if no About page exists.

### [MAJOR] Product Detail Page ID 1 Cart Link May Lack Accessible Name
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** The shopping cart link appears to have no visible text or accessible label in the shown DOM, which may leave the link without a meaningful accessible name for screen reader users.
- **Recommended Fix:** Add an accessible name such as `aria-label="Shopping cart"` or include descriptive visually hidden text inside the link.

### [MAJOR] Product Detail Page ID 4 Cart Link May Lack Accessible Name
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=4
- **Description:** The shopping cart link appears to be icon-only and no accessible name is visible in the provided DOM snippet. Screen reader users may not understand the link opens the cart.
- **Recommended Fix:** Provide an accessible name, such as `aria-label="Shopping cart"` or visually hidden text inside the link.

### [MAJOR] Product Detail Page ID 5 Cart Link Lacks Accessible Text
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=5
- **Description:** The shopping cart link appears to have no accessible text or aria-label in the DOM, making its purpose unclear to screen reader users.
- **Recommended Fix:** Add `aria-label="Shopping cart"` or visible/visually hidden text inside the link.

### [MAJOR] Product Detail Page ID 6 About Link Navigates to 404
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The `About` menu item links to a URL that is explicitly a 404 error page.
- **Recommended Fix:** Update the About link href to a valid About page URL or remove/disable the menu item if no About page exists.

### [MAJOR] Product Detail Page ID 6 Cart Link May Lack Accessible Name
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The shopping cart link appears to have no text content or explicit accessible name in the DOM fragment shown.
- **Recommended Fix:** Add an aria-label such as `aria-label="Shopping cart"` or include accessible text inside the link.

### [MAJOR] Product Sort Dropdown Does Not Apply Price Low-to-High Sorting
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Selecting an option on `[data-test='product-sort-container']` produced no change in the page when testing product sorting by price low to high.
- **Recommended Fix:** Verify the dropdown change handler and sorting logic. Ensure selecting price low-to-high reorders product cards correctly.

### [MAJOR] Product Sort Dropdown Still Has No Effect on Retry
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Retrying the sort interaction using the visible option label on `[data-test='product-sort-container']` again produced no page change.
- **Recommended Fix:** Validate both value-based and label-based selection paths and confirm the product list re-renders after sort selection.

### [MAJOR] Checkout Continue Button Does Not Trigger Missing Postal Code Validation
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Clicking `[data-test='continue']` with postal code missing produced no page change or expected validation response.
- **Recommended Fix:** Ensure Continue triggers validation for all required fields and displays a clear Postal Code required error when postal code is missing.

### [MAJOR] Checkout Continue Button Repeatedly Fails Missing Postal Code Validation Scenario
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** A repeated attempt to submit with postal code missing using `[data-test='continue']` produced no change, preventing validation feedback from being confirmed.
- **Recommended Fix:** Review the Continue button event handler and form validation flow. Add test coverage for each required-field error state.

## Minor Findings
- https://www.saucedemo.com/inventory-item.html?id=3 — Product photo appears cropped at the top, with the hanger partially cut off.
- https://www.saucedemo.com/inventory.html — `Dynamic Catalog` declares `aria-controls="dynamic_catalog_submenu"` but the referenced element is missing.
- https://www.saucedemo.com/inventory.html — Menu open/close icon images expose duplicate alt text despite adjacent buttons providing accessible names.
- https://www.saucedemo.com/cart.html — `Dynamic Catalog` has an invalid `aria-controls` reference to a missing submenu element.
- https://www.saucedemo.com/cart.html — Hamburger menu icon has redundant `alt="Open Menu"` while the button already provides the accessible name.
- https://www.saucedemo.com/checkout-step-one.html — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/checkout-step-one.html — Required checkout fields lack `required` or `aria-required` attributes.
- https://www.saucedemo.com/checkout-step-one.html — Error message container lacks `role="alert"` or `aria-live`, so screen readers may not announce validation errors.
- https://www.saucedemo.com/inventory-item.html?id=1 — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/inventory-item.html?id=1 — Menu button does not expose `aria-expanded` or `aria-controls`.
- https://www.saucedemo.com/inventory-item.html?id=1 — Decorative menu icons use non-empty alt text, causing duplicate announcements.
- https://www.saucedemo.com/inventory-item.html?id=2 — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/inventory-item.html?id=3 — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/inventory-item.html?id=3 — Sidebar actions use anchors with `href="#"` and `role="button"` instead of native buttons or valid links.
- https://www.saucedemo.com/inventory-item.html?id=4 — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/inventory-item.html?id=4 — Menu open/close icons expose redundant alt text.
- https://www.saucedemo.com/inventory-item.html?id=5 — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/inventory-item.html?id=5 — Menu toggle button lacks `aria-expanded` and `aria-controls`.
- https://www.saucedemo.com/inventory-item.html?id=5 — Open menu icon duplicates button accessible text.
- https://www.saucedemo.com/inventory-item.html?id=5 — Close menu icon duplicates button accessible text.
- https://www.saucedemo.com/inventory-item.html?id=6 — Open Menu button lacks expanded/collapsed state and controlled-menu relationship.
- https://www.saucedemo.com/inventory-item.html?id=6 — `Dynamic Catalog` has an invalid `aria-controls` reference.
- https://www.saucedemo.com/inventory-item.html?id=6 — Hamburger and close icons have duplicate non-empty alt text.
- https://www.saucedemo.com/inventory-item.html?id=6 — Several side menu actions use `href="#"` and `role="button"`, which may not behave consistently for keyboard users.

## Conclusion
The `problem_user` experience is significantly impaired by critical functional and UX defects. The checkout flow is unreliable, with incorrect field binding, persistent validation errors, and a non-functional Continue action. Inventory behavior is also affected by incorrect product images, broken sorting, and a failed add-to-cart action for Sauce Labs Onesie. Multiple pages contain sidebar `About` links that navigate to 404 pages, creating repeated high-impact navigation failures.

Recommended next steps:
1. Prioritize checkout form state management and Continue button routing defects.
2. Fix cart state handling for affected add-to-cart controls.
3. Correct sidebar `About` navigation across all pages.
4. Repair product image mappings and invalid item-not-found rendering.
5. Address recurring accessibility issues in navigation, ARIA references, cart link labels, and form validation announcements.
6. Add regression tests for checkout progression, sidebar navigation, product sorting, product image mapping, and accessibility attributes.