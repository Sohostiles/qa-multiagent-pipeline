# QA Automated Test Report

## Summary
This test report provides an evaluation of the Salsa application which was tested using the 'problem_user' role. The analysis covered multiple pages and highlighted various visual, functional, and UX issues impacting user experience and accessibility. A total of 18 issues were identified: 6 major and 12 minor, with no critical issues detected.

## Test Details
- Target Application: https://www.saucedemo.com
- User Role Tested: problem_user
- Pages Analysed: Inventory, Product Detail, Cart, Checkout Step One
- Total Issues Found: 18
  - Critical: 0 | Major: 6 | Minor: 12

## Critical & Major Findings

### [MAJOR] Identical Images for Different Products
- **Type:** visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** Identical images are utilized for different products, potentially causing user confusion.
- **Recommended Fix:** Ensure unique images are assigned to each product entry.

### [MAJOR] Footer Icons Lack Visible Labels
- **Type:** ux
- **Page:** https://www.saucedemo.com/inventory-item.html?id=5
- **Description:** Footer social media icons are missing visible labels, impairing screen reader functionality.
- **Recommended Fix:** Add descriptive labels to each social media icon to enhance accessibility.

### [MAJOR] 'Add to Cart' Button Feedback
- **Type:** functional
- **Page:** https://www.saucedemo.com/inventory-item.html?id=5
- **Description:** 'Add to cart' button lacks visual feedback or confirmation message, contributing to uncertainty about the action's success.
- **Recommended Fix:** Implement a confirmation message or button state change post-click for improved user feedback.

### [MAJOR] Poor Contrast on Cart Buttons
- **Type:** visual
- **Page:** https://www.saucedemo.com/cart.html
- **Description:** Low contrast between text and button backgrounds ('Continue Shopping' and 'Checkout') reduces readability.
- **Recommended Fix:** Adjust button text and background contrast to meet accessibility standards.

### [MAJOR] Action Buttons Lack Feedback
- **Type:** functional
- **Page:** https://www.saucedemo.com/cart.html
- **Description:** 'Continue Shopping' and 'Checkout' buttons do not provide visual feedback upon hover or click, reducing usability.
- **Recommended Fix:** Introduce hover and click state visuals to provide user feedback.

### [MAJOR] Input Error Validation
- **Type:** functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** Lack of feedback or validation for errors in input fields could cause user confusion.
- **Recommended Fix:** Implement real-time input validation with error messages to guide user correction.

## Minor Findings
- Non-descriptive alt text for product images may be required for accessibility.
- Copyright year incorrectly stated as 2026.
- Misaligned product image and text.
- Low contrast and inconsistent button alignment.
- Lack of detailed product information and input field placeholders.
- Visual layout issues related to buttons and headings.

## Conclusion
Overall, the application demonstrates potential usability and accessibility challenges primarily related to visual distinction and user feedback on actions. The recommended next steps include addressing major issues, particularly those affecting functional and primary user tasks, enhancing image handling, and improving accessibility features for a more inclusive user experience.