# QA Automated Test Report

## Summary
The test run for Saucedemo focused on the user role 'problem_user' across key pages. The test identified 75 issues, with significant findings highlighting major functional, visual, and accessibility concerns. Critical issues need immediate attention to ensure basic functionality, whereas major issues predominantly involve broken links and visual inconsistencies.

## Test Details
- Target Application: https://www.saucedemo.com
- User Role Tested: problem_user
- Pages Analysed: Inventory, Cart, Checkout Step One, Inventory Item
- Total Issues Found: 75
- Critical: 3 | Major: 44 | Minor: 28

## Critical & Major Findings

### CRITICAL Functional Issue: Broken 'All Items' Sidebar Link
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Clicking the 'All Items' link in the sidebar did not redirect to the inventory page; it simply opened the menu without any page change.
- **Recommended Fix:** Ensure the 'All Items' link navigates back to the inventory page by setting a correct href attribute or implementing navigational logic.

### CRITICAL Visual Issue: Incorrect Price Display
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** Price is displayed as '$√-1', not as a valid currency amount.
- **Recommended Fix:** Verify and correct the price retrieval from the database to display the correct format.

### CRITICAL Functional Issue: 'About' Link 404 Error
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The 'About' link in the hamburger menu leads to a 404 error page.
- **Recommended Fix:** Update the href to direct users to a valid 'about' page.

### MAJOR Functional Issue: Non-functional Sort and Add to Cart
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Interactions with 'select' sorting and 'add-to-cart' buttons did not produce the expected changes.
- **Recommended Fix:** Ensure all interactive elements perform their intended actions by updating event handlers or fixing the UI logic.

### MAJOR Visual Issue: Duplicate and Unrelated Product Images
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Images are identical and do not match product descriptions, with all images showing an unrelated dog instead.
- **Recommended Fix:** Update product images to accurately reflect each listing.

### MAJOR Accessibility Issue: Inaccessible Sidebar Links
- **Type:** accessibility
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Sidebar links have tabIndex set to -1, making them inaccessible via keyboard navigation.
- **Recommended Fix:** Remove or correct tabIndex attributes to allow keyboard focus and navigation.

### MAJOR Functional Issue: Form Submission Fails with Empty Fields
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The form does not process submission when fields are left empty, but no error message appears to guide users.
- **Recommended Fix:** Implement error messages for incomplete fields and enhance validation.

## Minor Findings
- Footer text contrast issues
- Header and menu button misalignments
- Button text overlapping
- Accessibility labels missing
- Visual alignment discrepancies

## Conclusion
The test revealed critical and major issues predominantly focused on functional disruptions and visual misrepresentations, particularly in navigation links and product details. Immediate resolution of critical issues is required to restore basic functionality and improve user experience. Suggested next steps include addressing broken links, ensuring visual consistency, and improving accessibility for a seamless customer interaction. Regular UI audits should also be incorporated to prevent future regressions.