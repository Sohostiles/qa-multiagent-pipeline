# QA Automated Test Report

## Summary
The test run evaluated the E-commerce site "SauceDemo" focusing on the functionalities for a visual user role. A total of 69 issues were identified, with significant concerns around functional, visual, and accessibility aspects hindering user experience and operational flow.

## Test Details
- Target Application: [https://www.saucedemo.com](https://www.saucedemo.com)
- User Role Tested: visual_user
- Pages Analysed: Inventory, Cart, Checkout Step One, Item Details
- Total Issues Found: 69
  - Critical: 7 | Major: 33 | Minor: 29

## Critical & Major Findings

### CRITICAL Issue: Products Not Sorted by Price
- **Type:** Functional
- **Page:** [https://www.saucedemo.com/inventory.html](https://www.saucedemo.com/inventory.html)
- **Description:** Products are not sorted by Price (low to high) based on displayed prices.
- **Recommended Fix:** Correct sorting functionality to reorganize products by ascending price.

### CRITICAL Issue: Menu Keyboard Accessibility
- **Type:** Accessibility
- **Page:** [https://www.saucedemo.com/inventory.html](https://www.saucedemo.com/inventory.html)
- **Description:** Menu items have `tabindex="-1"`, preventing keyboard access.
- **Recommended Fix:** Adjust `tabindex` to allow keyboard navigation when menu is open.

### CRITICAL Issue: Shopping Cart Screen Reader Access
- **Type:** Accessibility
- **Page:** [https://www.saucedemo.com/inventory.html](https://www.saucedemo.com/inventory.html)
- **Description:** Shopping cart link lacks an accessible name for screen readers.
- **Recommended Fix:** Add an `aria-label` to describe the cart link's function.

### CRITICAL Issue: Checkout Error Message
- **Type:** Functional
- **Page:** [https://www.saucedemo.com/checkout-step-one.html](https://www.saucedemo.com/checkout-step-one.html)
- **Description:** No error message displayed when attempting to continue with empty fields.
- **Recommended Fix:** Ensure appropriate error messages appear for form validations.

### MAJOR Issue: Sorting Dropdown Mismatch
- **Type:** UX
- **Page:** [https://www.saucedemo.com/inventory.html](https://www.saucedemo.com/inventory.html)
- **Description:** Price dropdown displays 'Price (low to high)' but items are not sorted accordingly.
- **Recommended Fix:** Ensure item sorting matches dropdown selection.

### MAJOR Issue: Cart Icon Badge Count
- **Type:** Visual
- **Page:** [https://www.saucedemo.com/inventory.html](https://www.saucedemo.com/inventory.html)
- **Description:** Cart icon badge shows the wrong item count, confusing user perception.
- **Recommended Fix:** Synchronize the cart number with actual items added.

### MAJOR Issue: Menu Button Non-responsiveness
- **Type:** Functional
- **Page:** [https://www.saucedemo.com/inventory.html](https://www.saucedemo.com/inventory.html)
- **Description:** Menu button does not visibly open the menu.
- **Recommended Fix:** Ensure menu button opens the navigation menu visibly upon interaction.

## Minor Findings
- Text misalignment and readability issues in product titles and buttons.
- Overlapping UI elements causing clutter at various locations, such as navigation buttons.
- Incorrect or outdated copyright information.
- Minimal contextual alt attributes on images and icons failing to aid visually impaired users adequately.

## Conclusion
The identified issues, especially critical and major ones, highlight pressing challenges with the site's accessibility and functional operations. Immediate attention to address sorting issues, menu functionality, and accessibility barriers is recommended to enhance the user experience and comply with accessibility standards. Comprehensive testing following these rectifications will aid in optimizing usability and ensure smoother customer interactions.