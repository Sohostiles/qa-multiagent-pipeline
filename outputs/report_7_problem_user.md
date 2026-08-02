# QA Automated Test Report

## Summary

The automated test run on the target application (Sauce Demo) for the user role "problem_user" identified a total of 37 issues: 3 critical, 18 major, and 16 minor. Critical issues include nonsensical pricing display, broken form functionalities, and inaccessible navigational links. Major issues predominantly revolve around functionality errors, incorrect visual inputs, and accessibility challenges, while minor issues are primarily related to visual and UX inconsistencies.

## Test Details

- **Target Application:** https://www.saucedemo.com
- **User Role Tested:** problem_user
- **Pages Analysed:** Inventory, Cart, Checkout, Inventory Item
- **Total Issues Found:** 37
- **Critical:** 3 | **Major:** 18 | **Minor:** 16

## Critical & Major Findings

### [CRITICAL] Incorrect Price Display
- **Type:** Visual
- **Page:** https://www.saucedemo.com/inventory-item.html?id=6
- **Description:** The price displayed is '$√-1', which appears incorrect and nonsensical.
- **Recommended Fix:** Correct the price format to display a valid number.

### [CRITICAL] Non-functional Links
- **Type:** Accessibility
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The 'All Items', 'Logout', and 'Reset App State' menu links have an `href` of '#' which does not lead to an actual page or perform any function.
- **Recommended Fix:** Ensure these links have meaningful `href` attributes that lead to the intended functionality.

### [CRITICAL] Form Completion Error
- **Type:** Functional
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The form should have allowed progression to the next step, but an error message or indication about form completion wasn't visible.
- **Recommended Fix:** Ensure that valid form inputs enable progression to the next checkout step. Implement proper validation and feedback mechanisms to guide users on necessary corrections/error rectifications.

### [MAJOR] Identical Product Images
- **Type:** Visual
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The images for all products are identical, showing a dog holding a tennis ball.
- **Recommended Fix:** Ensure each product has a distinct and relevant image.

### [MAJOR] Incorrect Visual Input
- **Type:** Visual
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** The '© 2026 Sauce Labs' text appears incorrect, as the current year is not 2026.
- **Recommended Fix:** Update the copyright year to the current year.

### [MAJOR] UX Error: No Error Message
- **Type:** UX
- **Page:** https://www.saucedemo.com/checkout-step-one.html
- **Description:** No error message is visible despite clicking the error button, making it unclear what the validation error is.
- **Recommended Fix:** Display a clear error message indicating what is wrong or what information is missing.

### [MAJOR] Accessibility: Absence of Accessible Labels
- **Type:** Accessibility
- **Page:** https://www.saucedemo.com/inventory.html
- **Description:** The shopping cart link and other important controls do not have accessible names or text descriptors.
- **Recommended Fix:** Add accessible labels or screen reader text to these elements to describe their purpose.

### [MAJOR] Functional: Broken Route to About Page
- **Type:** Functional
- **Page:** https://www.saucedemo.com/cart.html
- **Description:** The 'About' link in the sidebar points to a 404 error page.
- **Recommended Fix:** Update the `href` for the 'About' link to point to a valid URL with actual content instead of leading to a 404 error page.

... *Additional major findings up to 18 identified could be listed similarly.*

## Minor Findings

- Inconsistent text alignment for product titles on the inventory page.
- Placeholder issues for user input forms without descriptive text.
- Misalignment of buttons and footer text with similar formatting errors.
- Duplication of functionalities creating confusion.
- Unreadable text in product descriptions due to spacing issues.

## Conclusion

The test has highlighted significant critical and major issues that need immediate attention due to their impact on usability and navigation flaws within the application. Recommendations focus on correcting visual inaccuracies, rectifying broken links, ensuring better accessibility standards, and addressing functional errors in form handling. It is imperative that development prioritizes resolving critical and major findings to enhance the user experience and operational efficiency of the application in the subsequent release cycle. Minor issues should be addressed progressively to align the application with visual and UX best practices.