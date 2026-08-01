# QA Automated Test Report

## Summary
This report covers an automated test conducted on the Sauce Demo website (https://www.saucedemo.com) using the role of 'standard_user'. A total of 34 issues were identified, comprising 2 critical issues, 15 major issues, and 17 minor issues.

## Test Details
- Target Application: Sauce Demo (https://www.saucedemo.com)
- User Role Tested: standard_user
- Pages Analysed: Inventory, Cart, Checkout Steps
- Total Issues Found: 34
  - Critical: 2 | Major: 15 | Minor: 17

## Critical & Major Findings

### CRITICAL Functional Issue
- **Type:** Functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** No error message is displayed when submitting empty form fields.
- **Recommended Fix:** Display an appropriate error message in the '.error-message-container' when form fields are submitted empty.

### CRITICAL Accessibility Issue
- **Type:** Accessibility
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The shopping cart link is present but does not contain any accessible name or text.
- **Recommended Fix:** Add an aria-label or inner text to provide an accessible name for the element.

### MAJOR Visual Issue
- **Type:** Visual
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The field for the zip/postal code is not filled out, potentially blocking the 'Continue' button functionality.
- **Recommended Fix:** Ensure all necessary fields are filled before enabling the 'Continue' button.

### MAJOR UX Issue
- **Type:** UX
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The sidebar menu is not visible as expected upon interaction to reopen the menu.
- **Recommended Fix:** Ensure the sidebar menu appears when the menu button is clicked.

### MAJOR Accessibility Issue
- **Type:** Accessibility
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The menu button and close menu button lack aria-expanded attributes to indicate their states.
- **Recommended Fix:** Add aria-expanded attributes which dynamically update based on the state of the menu.

### MAJOR Functional Issue
- **Type:** Functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Form fields are not validated correctly, and the error message is not shown.
- **Recommended Fix:** Ensure that an appropriate error message is displayed within the 'error-message-container' to inform the user that all fields are required and cannot be empty.

## Minor Findings
- Cart icon number visibility issues on various pages.
- Visual alignment of product images and text.
- Low contrast in text colors on product cards.
- Button text not vertically centered.
- Footer text contrast is too low for readability.
- Sidebar links point to ineffective URLs.
- Header elements not aligned properly.
- Form input labels missing for increased accessibility.
- Overlapping elements within page headers.

## Conclusion
The test revealed critical accessibility and functional issues, alongside a range of major and minor issues that affect user experience, accessibility, and visual consistency across the site. It is recommended to prioritize fixing the critical issues to ensure basic functionality and accessibility. Subsequently, address major issues to enhance user experience and perform detailed visual inspections to resolve minor issues. Continuous accessibility audits are also recommended to ensure compliance with WCAG standards.