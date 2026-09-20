# QA Automated Test Report

## Summary
Automated QA testing was performed against Sauce Demo using the `problem_user` role. The run identified 53 total issues across inventory, cart, checkout, and product detail pages. Key risks include broken checkout progression, incorrect cart behavior, broken About navigation, mismatched product imagery, invalid item-not-found states, and inconsistent checkout form validation. Several minor accessibility and visual-state issues were also detected.

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
- Total Issues Found: 53
- Critical: 10 | Major: 19 | Minor: 24

## Critical & Major Findings

### [MAJOR] Incorrect Product Thumbnails Displayed Across Inventory Grid
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** All six product thumbnails show the same cropped dog photo, which does not match the listed product names such as Backpack, Bike Light, T-Shirt, Jacket, or Onesie. The repeated/mismatched image makes the product catalog visually incorrect.
- **Recommended Fix:** Restore the correct product image asset for each inventory item and verify the image URL or data mapping so each product displays its intended thumbnail.

### [MAJOR] Duplicate Dog Image Used for All Inventory Products
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** All six product cards display the same pug/dog photo, and the image does not match the product names such as Backpack, Bike Light, T-Shirt, Jacket, Onesie, and T-Shirt Red. This makes the product catalog visually incorrect even though images are present.
- **Recommended Fix:** Update the product image source mapping so each inventory item displays its correct corresponding product image instead of the duplicated dog image.

### [MAJOR] Checkout Error Message Remains “First Name is Required” After First Name Is Entered
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The form shows the First Name field filled with “Test”, but the validation banner still says “Error: First Name is required.” This is contradictory and suggests the validation message did not update after the user entered a valid first name.
- **Recommended Fix:** Update the validation state immediately after the First Name field becomes valid. If another required field is missing, display the next relevant validation message, such as Last Name or Postal Code required.

### [MAJOR] First Name Field Remains in Error State Despite Valid Value
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The First Name input appears in an error state, with a red underline and error icon, even though it contains the entered value “Test”.
- **Recommended Fix:** Clear the error styling and error icon from the First Name field once it contains a valid value.

### [MAJOR] Valid First Name Field Marked Invalid While Last Name Error Is Displayed
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The valid First Name field containing “Test” is still styled as an error, with a red underline and error icon, even though the displayed validation message says only the Last Name is required.
- **Recommended Fix:** Apply error styling and icons only to the field currently failing validation, or clear the error state from First Name once it has a valid value.

### [CRITICAL] Last Name Entry Does Not Populate the Last Name Field
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** After entering “User” into the Last Name field, the Last Name field still appears empty and invalid, and the page continues to display “Error: Last Name is required.” The visible value “User” appears in the top input field instead, suggesting the entered value is being rendered in the wrong field.
- **Recommended Fix:** Ensure the `[data-test='lastName']` input receives and displays the entered value. Validation should clear or update the Last Name error once a valid value is present.

### [MAJOR] First Name Validation Message Remains Stale After Value Is Entered
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The validation banner still says “Error: First Name is required” even though the First Name field visibly contains “John”. This is a stale and inconsistent validation state after the user filled the field.
- **Recommended Fix:** Clear or update the validation message when the First Name field is populated. If other required fields are empty, show the next relevant error.

### [CRITICAL] Last Name Value Appears in First Name Field
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** After filling the Last Name field with “Doe”, the value appears in the top field, which is the First Name field, while the Last Name field still appears empty. This also conflicts with the displayed error message “Error: First Name is required”, because the field that appears to be First Name contains text.
- **Recommended Fix:** Ensure values entered into the Last Name input are rendered only in the Last Name field. Synchronize validation messages with the actual field values and DOM input state.

### [MAJOR] First Name Field Contains Value But Still Triggers Required Error
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The First Name field appears to contain “Doe”, but the form still displays “Error: First Name is required” and marks the field with an error state. This is visually inconsistent and misleading.
- **Recommended Fix:** Ensure validation uses the current value of the First Name field and clears the first-name-required error once the field is populated, or display the correct missing-field error.

### [MAJOR] Completed First Name and Postal Code Fields Marked Invalid
- **Type:** ux
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The First Name and Postal Code fields contain values but are visually marked with red underline styling and red error icons, even though the displayed error message only says the Last Name is required. This makes valid fields appear invalid.
- **Recommended Fix:** Only apply error styling and error icons to the specific invalid field, or clearly indicate all fields that are invalid with accurate messaging.

### [MAJOR] Bolt T-Shirt Detail Image Does Not Match Product Description
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** The product image appears to show a plain dark/black T-shirt with no visible red bolt graphic, while the product title and description identify it as the “Sauce Labs Bolt T-Shirt” with a red bolt. The expected design/logo appears to be missing from the displayed product image.
- **Recommended Fix:** Verify the product image asset for this item and replace it with the correct Bolt T-Shirt image showing the red bolt graphic, or update the product text if the plain shirt is intentional.

### [MAJOR] Red T-Shirt Detail Image Displays Incorrect Product Type
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=3
- **Description:** The product name and description identify the item as a red T-shirt, but the displayed product image appears to be a long-sleeve sweatshirt or sweater. This creates a visible mismatch between the product image and product text.
- **Recommended Fix:** Use an image that accurately shows the red T-shirt, or update the product name and description to match the displayed sweatshirt.

### [CRITICAL] Item-Not-Found Page Displays Invalid Price
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The item-not-found state displays a nonsensical price, “$√-1”, which appears invalid and confusing to users.
- **Recommended Fix:** Remove the price from the item-not-found state or replace it with a clear message that the item is unavailable.

### [MAJOR] Add to Cart Button Displayed for Item Not Found
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** An “Add to cart” button is shown for an item that is explicitly labeled “ITEM NOT FOUND”. This creates a misleading purchase action for an unavailable or nonexistent product.
- **Recommended Fix:** Hide or disable the Add to Cart button when the item cannot be found, and provide only navigation back to the products page.

### [MAJOR] About Menu Link Navigates to 404 from Inventory Page
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The About menu item points directly to an error/404 URL, so activating it will navigate users to an error page instead of an About page.
- **Recommended Fix:** Update the About link `href` to the correct About page URL, or remove/disable the link if no About page exists.

### [MAJOR] About Menu Link Navigates to 404 from Cart Page
- **Type:** functional
- **Page:** https://www.saucedemo.com/cart.html
- **Description:** The About menu item points directly to a 404 error URL, so selecting it will navigate users to an error page instead of a valid About page.
- **Recommended Fix:** Update the About link `href` to a valid About page URL, or remove/disable the menu item if no About page is available.

### [MAJOR] About Menu Link Navigates to 404 from Checkout Page
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The About menu item points directly to a 404 error URL, so activating it will navigate the user to an error page rather than a valid About page.
- **Recommended Fix:** Update the About link `href` to a valid destination, such as the intended Sauce Labs About page, or remove/disable the link if no destination exists.

### [MAJOR] About Menu Link Navigates to 404 from Product Detail Page ID 1
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** The About menu item points directly to an error/404 URL, so activating it would take the user to a not-found page instead of an About page.
- **Recommended Fix:** Update the `href` to the correct About page URL, or remove/disable the menu item if no About page exists.

### [MAJOR] Sidebar Menu Items Use Non-Functional `href="#"` Targets on Product Detail Page ID 1
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** Several side menu items use `href="#"` as their destination and rely on button-like behavior. If JavaScript handling fails or is unavailable, these controls lead nowhere. Anchors with `href="#"` are also not semantically correct for action-only controls.
- **Recommended Fix:** Use real `href` values for navigation links, and use button elements for actions such as Logout, Reset App State, and submenu toggling.

### [CRITICAL] About Menu Link Navigates to 404 from Product Detail Page ID 2
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=2
- **Description:** The About menu item points directly to a 404 error URL, so activating it will take users to an error page instead of a valid About page.
- **Recommended Fix:** Update the About link `href` to a valid About page URL, or remove/disable the menu item if no About page exists.

### [CRITICAL] About Menu Link Navigates to 404 from Product Detail Page ID 3
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=3
- **Description:** The About menu item points directly to a 404 error URL, so activating it would lead users to a broken page instead of the expected About destination.
- **Recommended Fix:** Update the About link `href` to a valid About page URL, or remove/disable the link if no About page is available.

### [CRITICAL] About Menu Link Navigates to 404 from Product Detail Page ID 4
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=4
- **Description:** The About menu item links directly to a 404 error URL, so selecting it will take users to an error page instead of a valid About page.
- **Recommended Fix:** Update the `href` to a valid About destination, such as the correct Sauce Labs About page, or remove the menu item if no About page exists.

### [MAJOR] Sidebar Menu Items Use Non-Functional `href="#"` Targets on Product Detail Page ID 4
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=4
- **Description:** Several sidebar menu actions are implemented as anchor elements with `href="#"`, meaning their native destination is the current page rather than a real route or action target. This can cause controls to appear to lead nowhere if JavaScript handling fails and is inappropriate for action-only controls.
- **Recommended Fix:** Use real `href` values for navigation links, and use button elements for actions such as logout, reset, or submenu expansion, with appropriate click and keyboard handling.

### [CRITICAL] About Menu Link Navigates to 404 from Product Detail Page ID 5
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=5
- **Description:** The About menu item points to a 404 error URL, so selecting it will not take the user to a valid About page.
- **Recommended Fix:** Update the About link `href` to a valid destination, or implement the target page so the URL does not return a 404.

### [CRITICAL] About Menu Link Navigates to 404 from Product Detail Page ID 6
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The About menu link points directly to an error/404 URL, so activating it will take users to a broken page instead of an About page.
- **Recommended Fix:** Update the `href` to a valid About page URL, or remove/disable the link if no About page is available.

### [CRITICAL] Sauce Labs Backpack Add to Cart Control Has No Effect
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Clicking the Sauce Labs Backpack Add to Cart control appears to leave the page state unchanged. The product should be added to the cart, the cart badge should update to show one item, and the product control should change from Add to Cart to Remove.
- **Recommended Fix:** Ensure the Add to Cart handler updates the cart state for Sauce Labs Backpack, renders the cart badge count, and changes the item button to the Remove state after a successful click.

### [MAJOR] Product Sort Dropdown Has No Effect
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Selecting an option on `[data-test='product-sort-container']` produced no visible change in the page, though sorting items from low to high price was expected.
- **Recommended Fix:** Ensure the sort dropdown triggers the intended sorting logic, updates product ordering, and reflects the selected sort state.

### [MAJOR] Continue Button Has No Effect When Postal Code Is Missing
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Clicking `[data-test='continue']` produced no change in the page when submitting with the postal code missing. A required-field validation response was expected.
- **Recommended Fix:** Ensure the Continue button triggers checkout form validation and displays the correct required-field message for missing Postal Code.

### [CRITICAL] Continue Button Has No Effect with Completed Checkout Information
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Clicking `[data-test='continue']` produced no change in the page after checkout information was completed. The expected behavior is progression to the checkout overview page.
- **Recommended Fix:** Ensure the Continue button submits valid checkout information, persists the entered values, and routes the user to the checkout overview page.

## Minor Findings
- Zip/Postal Code field is marked invalid while the active validation message only references Last Name.
- Populated First Name fields remain styled with red underline/error icon in multiple checkout validation states.
- Populated Postal Code fields remain styled with red underline/error icon despite unrelated validation messages.
- First Name field containing “John” remains visually invalid.
- Checkout fields lack appropriate `autocomplete` attributes for First Name, Last Name, and Postal Code.
- Required checkout fields are not marked with `required` or `aria-required`.
- Dynamic Catalog menu item references `aria-controls="dynamic_catalog_submenu"` across multiple pages, but no matching element exists in the DOM.
- Burger menu open button does not expose `aria-expanded` or `aria-controls`.
- Open and close menu icon images use alt text that duplicates adjacent button labels, causing redundant screen reader announcements.
- Similar duplicate menu-icon alt text issues occur on inventory and multiple product detail pages.
- Sidebar menu accessibility relationships should be corrected consistently across inventory, cart, checkout, and product detail pages.

## Conclusion
The `problem_user` experience is significantly impaired by both functional and UX defects. The most urgent issues are the broken checkout progression, incorrect field value handling in checkout, non-functional Add to Cart behavior, and About links that route users to 404 pages. Product image mismatches also reduce catalog trust and create confusion during browsing.

Recommended next steps:
1. Prioritize critical functional defects affecting checkout, cart state, and broken navigation.
2. Correct checkout input binding and validation-state synchronization.
3. Repair product image mappings for inventory and product detail pages.
4. Resolve invalid item-not-found behavior by removing purchase actions and invalid pricing.
5. Apply accessibility fixes to sidebar menu controls and checkout fields.
6. Re-run the automated suite for `problem_user` after fixes and add regression tests for cart, checkout, menu navigation, sorting, and product image mapping.