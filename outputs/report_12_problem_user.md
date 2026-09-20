# QA Automated Test Report

## Summary
The QA automated test run conducted on the target application at `https://www.saucedemo.com` has surfaced several issues across different categories: critical, major, and minor. The test focused on the 'problem_user' role and covered multiple pages of the application. A total of 68 issues were detected, comprising 5 critical issues, 36 major issues, and 26 minor issues.

## Test Details
- Target Application: https://www.saucedemo.com
- User Role Tested: problem_user
- Pages Analysed: 
  - Inventory
  - Inventory Item
  - Checkout Step One
  - Cart
- Total Issues Found: 68
- Critical: 5 | Major: 36 | Minor: 26

## Critical & Major Findings

### CRITICAL Issue: First Name Field Missing
- **Type:** visual
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The 'First Name' input field is not visible or missing on the form.
- **Recommended Fix:** Ensure the 'First Name' input field is visible and included in the form for proper data entry.

### CRITICAL Issue: Invalid Price Display
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The price of the item is displayed as '$√-1', which is invalid.
- **Recommended Fix:** Ensure that the price of the item is correctly fetched and displayed as a valid monetary value.

### CRITICAL Issue: Form Submission Failure
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Form submission failed to proceed to the next step due to missing last name input.
- **Recommended Fix:** Make sure all required fields are filled before submission and provide clear user feedback for missing fields.

### CRITICAL Issue: No Validation Error Messages
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** No validation error messages are displayed when attempting to continue with all fields empty.
- **Recommended Fix:** Display appropriate error messages for each required form field when it is left empty.

### CRITICAL Issue: Invalid 'About' Link
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=1
- **Description:** The 'About' link in the menu redirects to a 404 error page.
- **Recommended Fix:** Update the href to point to a valid URL or remove the link if not in use.

### MAJOR Issue: Duplicate Product Images
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Identical product images used for all listed items could confuse users.
- **Recommended Fix:** Use unique images for each product to better differentiate them.

### MAJOR Issue: Menu Functionality
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The menu does not appear open after clicking the menu button.
- **Recommended Fix:** Ensure clicking the menu button opens the menu overlay with accessible options.

### MAJOR Issue: Error Message Visibility
- **Type:** visual
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** No visible error message after clicking the error button, although intended to.
- **Recommended Fix:** Ensure that clicking the error button properly displays an error message on the screen.

### MAJOR Issue: Functional Sidebar Links
- **Type:** functional
- **Page:** Various
- **Description:** Links in the sidebar lead to 404 pages or have href attributes set to '#', making them non-functional.
- **Recommended Fix:** Correct the href attributes to lead to valid pages or ensure JavaScript functionality.

### MAJOR Issue: Accessibility - Menu Items
- **Type:** accessibility
- **Page:** https://www.saucedemo.com/cart.html
- **Description:** Menu items are set with 'tabindex' value of '-1', removing them from the tab order.
- **Recommended Fix:** Remove 'tabindex="-1"' to ensure inclusion in the natural tab order.

## Minor Findings
- Repetitive product images for minor products.
- Low contrast and readability issues with placeholder and footer text.
- Layout misalignments, such as overlapping text and misaligned social media icons.
- Lack of ARIA labels, alt attributes, and proper tabindex settings for accessibility.

## Conclusion
The test run highlighted several critical and major issues that need immediate attention, especially those affecting functionality and visual presentation of key pages like the checkout and product details. Addressing these issues will improve user experience and accessibility. The next steps should focus on fixing critical and major issues, particularly around form field visibility, link functionality, and error message handling, followed by addressing minor accessibility concerns. Regular QA audits should be implemented to maintain and improve software quality.