# QA Automated Test Report

## Summary
This automated test run was conducted on the Saucedemo application using a performance_glitch_user role. A total of 74 issues were identified, comprising 3 critical, 36 major, and 35 minor issues. The findings primarily focused on visual, functional, and accessibility concerns affecting the user experience.

## Test Details
- Target Application: https://www.saucedemo.com
- User Role Tested: performance_glitch_user
- Pages Analysed: All major user-facing pages
- Total Issues Found: 74
- Critical: 3 | Major: 36 | Minor: 35

## Critical & Major Findings

### [CRITICAL] Button Lacks Accessible Name
- **Type:** accessibility
- **Page:** https://www.saucedemo.com/inventory-item.html?id=0
- **Description:** The button with id 'react-burger-menu-btn' lacks an accessible name, impairing users with assistive technologies.
- **Recommended Fix:** Add an aria-label attribute or other accessible text to the button to describe its action.

### [CRITICAL] Missing Alt Attribute
- **Type:** accessibility
- **Page:** https://www.saucedemo.com/inventory-item.html?id=0
- **Description:** No alt attribute on image elements inside the anchor with class 'bm-item menu-item'.
- **Recommended Fix:** Add descriptive alt text to img elements for accessibility.

### [CRITICAL] Primary Button Lacks Accessible Name
- **Type:** accessibility
- **Page:** https://www.saucedemo.com/inventory-item.html?id=0
- **Description:** The primary button with class 'bm-burger-button' lacks an accessible name.
- **Recommended Fix:** Add aria-label or inner text to the button for better accessibility.

### [MAJOR] Incorrect Price Sorting
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Products are not correctly sorted according to 'Price (low to high)'.
- **Recommended Fix:** Ensure the sorting function arranges items from lowest to highest price smartly.

### [MAJOR] Non-Functional Menu Links
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Menu links 'All Items', 'Logout', and 'Reset App State' have hrefs set to '#' leading nowhere.
- **Recommended Fix:** Ensure href attributes lead to actual destinations or trigger appropriate functions.

### [MAJOR] Sidebar Menu Overlapping with Content
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Sidebar content overlaps the main inventory content.
- **Recommended Fix:** Adjust the z-index or layout positioning.

### [MAJOR] Missing Error Display
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Error handling lacks visible error messages post interaction.
- **Recommended Fix:** Display descriptive error messages prominently when a form error occurs.

### [MAJOR] Inaccessible Menu Navigation
- **Type:** accessibility
- **Page:** https://www.saucedemo.com/inventory-item.html?id=5
- **Description:** Menu items have tabindex set to -1, making them inaccessible via keyboard.
- **Recommended Fix:** Remove or appropriately set tabindex to allow keyboard navigation.

## Minor Findings
- Visual issues with button states and cart count discrepancies.
- Contrast and alignment concerns, affecting readability and page aesthetics.
- Missing visual emphasis on interactive elements like 'Finish' button.
- Text alignment and responsiveness optimization are required.
- Consistent use of appropriate HTML attributes in interactive elements should be ensured.

## Conclusion
While the test identified several critical and major issues primarily involving accessibility and functionality, resolving these can lead to significant improvements in user experience and performance. It is recommended to prioritize the fixes for critical and major issues, followed by addressing minor issues to enhance the overall application usability and accessibility. Regular regression testing should be conducted post-fixes to ensure stability and performance.