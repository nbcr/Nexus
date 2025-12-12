# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 288

**JavaScript Issues:** 134

## Issues by Severity

### 🔴 CRITICAL Issues (5)

#### app/static/js/FeedRenderer.js
- **Line 12:** Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)
- **Line 216:** Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed. (`javascript:S3776`)

#### app/static/js/HeaderAuth.js
- **Line 15:** Refactor this function to reduce its Cognitive Complexity from 56 to the 15 allowed. (`javascript:S3776`)

#### app/static/js/HeaderDarkMode.js
- **Line 45:** Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)

#### app/static/js/InfiniteFeed.js
- **Line 47:** Refactor this asynchronous operation outside of the constructor. (`javascript:S7059`)

---

### 🟠 BLOCKER Issues (2)

#### app/static/js/AdminAuth.js
- **Line 72:** Add the "let", "const" or "var" keyword to this declaration of "currentUser" to make it explicit. (`javascript:S2703`)

#### app/static/js/FeedArticleModal.js
- **Line 122:** Add the "let", "const" or "var" keyword to this declaration of "adsbygoogle" to make it explicit. (`javascript:S2703`)

---

### 🟡 MAJOR Issues (12)

#### app/static/js/FeedRenderer.js
- **Line 28:** Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 114:** Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 224:** Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 248:** Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)

#### app/static/js/FeedArticleModal.js
- **Line 75:** Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 122:** Extract the assignment of "adsbygoogle" from this expression. (`javascript:S1121`)

#### app/static/js/HeaderPreferences.js
- **Line 165:** Remove this useless assignment to variable "lastScrollTop". (`javascript:S1854`)

#### app/static/js/HoverTracker.js
- **Line 389:** 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)

---

### 🔵 MINOR Issues (115)

#### app/static/auth.js
- **Line 122:** Unexpected negated condition. (`javascript:S7735`)

#### app/static/js/FeedArticleModal.js
- **Line 122:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 235:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/FeedObservers.js
- **Line 54:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 128:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/FeedUtils.js
- **Line 212:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/GlobalScrollTracker.js
- **Line 84:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/HeaderAuth.js
- **Line 19:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 21:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 126:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 162:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 169:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 170:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 171:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 172:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/HeaderDarkMode.js
- **Line 114:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 115:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/HeaderMenu.js
- **Line 76:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 77:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/HeaderPreferences.js
- **Line 17:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 108:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 172:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 182:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 183:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 184:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/HeaderSession.js
- **Line 13:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 16:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 44:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 45:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 46:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/HoverTracker.js
- **Line 42:** Don't use a zero fraction in the number. (`javascript:S7748`)
- **Line 117:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 147:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 158:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 172:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 181:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 265:** Prefer `.at(…)` over `[….length - index]`. (`javascript:S7755`)
- **Line 280:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 297:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 353:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 385:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 389:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 394:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 474:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/InfiniteFeed.js
- **Line 55:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 57:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 66:** Prefer `globalThis` over `window`. (`javascript:S7764`) (2 instances)
- **Line 67:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 168:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 169:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 193:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 306:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/config.js
- **Line 3:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 51:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)

#### app/static/js/feed-notifier.js
- **Line 12:** Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 26:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 29:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 121:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)

---

## Summary by Priority

1. **🔴 CRITICAL (5 issues)** - Address immediately: Complex functions need refactoring
2. **🟠 BLOCKER (2 issues)** - Fix next: Missing variable declarations
3. **🟡 MAJOR (12 issues)** - Schedule soon: Code quality improvements
4. **🔵 MINOR (115 issues)** - Address gradually: Style and best practice improvements

## All JavaScript Issues (134)

### app/static/auth.js (1 issues)

- **Line 122:** [MINOR] Unexpected negated condition. (`javascript:S7735`)

### app/static/js/AdminAuth.js (1 issues)

- **Line 72:** [BLOCKER] Add the "let", "const" or "var" keyword to this declaration of "currentUser" to make it explicit. (`javascript:S2703`)

### app/static/js/FeedArticleModal.js (5 issues)

- **Line 75:** [MAJOR] Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 122:** [BLOCKER] Add the "let", "const" or "var" keyword to this declaration of "adsbygoogle" to make it explicit. (`javascript:S2703`)
- **Line 122:** [MAJOR] Extract the assignment of "adsbygoogle" from this expression. (`javascript:S1121`)
- **Line 122:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 235:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/FeedObservers.js (2 issues)

- **Line 54:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 128:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/FeedRenderer.js (6 issues)

- **Line 12:** [CRITICAL] Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)
- **Line 28:** [MAJOR] Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 114:** [MAJOR] Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 216:** [CRITICAL] Refactor this function to reduce its Cognitive Complexity from 28 to the 15 allowed. (`javascript:S3776`)
- **Line 224:** [MAJOR] Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 248:** [MAJOR] Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)

### app/static/js/FeedUtils.js (1 issues)

- **Line 212:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/GlobalScrollTracker.js (1 issues)

- **Line 84:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/HeaderAuth.js (9 issues)

- **Line 15:** [CRITICAL] Refactor this function to reduce its Cognitive Complexity from 56 to the 15 allowed. (`javascript:S3776`)
- **Line 19:** [MINOR] Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 21:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 126:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 162:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 169:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 170:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 171:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 172:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/HeaderDarkMode.js (3 issues)

- **Line 45:** [CRITICAL] Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)
- **Line 114:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 115:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/HeaderMenu.js (2 issues)

- **Line 76:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 77:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/HeaderPreferences.js (7 issues)

- **Line 17:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 108:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 165:** [MAJOR] Remove this useless assignment to variable "lastScrollTop". (`javascript:S1854`)
- **Line 172:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 182:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 183:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 184:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/HeaderSession.js (5 issues)

- **Line 13:** [MINOR] Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 16:** [MINOR] '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 44:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 45:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 46:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/HoverTracker.js (15 issues)

- **Line 42:** [MINOR] Don't use a zero fraction in the number. (`javascript:S7748`)
- **Line 117:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 147:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 158:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 172:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 181:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 265:** [MINOR] Prefer `.at(…)` over `[….length - index]`. (`javascript:S7755`)
- **Line 280:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 297:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 353:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 385:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 389:** [MAJOR] 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)
- **Line 389:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 394:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 474:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/InfiniteFeed.js (10 issues)

- **Line 47:** [CRITICAL] Refactor this asynchronous operation outside of the constructor. (`javascript:S7059`)
- **Line 55:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 57:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 66:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 66:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 67:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 168:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 169:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 193:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 306:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/config.js (2 issues)

- **Line 3:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 51:** [MINOR] '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)

### app/static/js/feed-notifier.js (12 issues)

- **Line 12:** [MINOR] Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 26:** [MINOR] Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 29:** [MINOR] '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 121:** [MINOR] Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 124:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 154:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 156:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 239:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 240:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 244:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 323:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 326:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/header.js (14 issues)

- **Line 24:** [MINOR] Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 27:** [MINOR] '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 43:** [CRITICAL] Refactor this function to reduce its Cognitive Complexity from 51 to the 15 allowed. (`javascript:S3776`)
- **Line 47:** [MINOR] Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 49:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 136:** [MINOR] Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 146:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 182:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 223:** [CRITICAL] Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)
- **Line 282:** [CRITICAL] Remove this use of the "void" operator. (`javascript:S3735`)
- **Line 402:** [MAJOR] Remove this useless assignment to variable "lastScrollTop". (`javascript:S1854`)
- **Line 409:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 426:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 517:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)

### app/static/js/history-tracker.js (3 issues)

- **Line 8:** [MINOR] Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 83:** [MINOR] Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 226:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/hover-tracker.js (14 issues)

- **Line 52:** [MINOR] Don't use a zero fraction in the number. (`javascript:S7748`)
- **Line 127:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 157:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 168:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 182:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 191:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 275:** [MINOR] Prefer `.at(…)` over `[….length - index]`. (`javascript:S7755`)
- **Line 290:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 307:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 363:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 395:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 399:** [MAJOR] 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)
- **Line 399:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 404:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/session.js (2 issues)

- **Line 49:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 49:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/trending.js (7 issues)

- **Line 20:** [MINOR] Unexpected negated condition. (`javascript:S7735`)
- **Line 86:** [MAJOR] Remove this useless assignment to variable "trendsHtml". (`javascript:S1854`)
- **Line 86:** [BLOCKER] Add a "return" statement to this callback. (`javascript:S3796`)
- **Line 86:** [MINOR] Remove the declaration of the unused 'trendsHtml' variable. (`javascript:S1481`)
- **Line 96:** [MINOR] `String.raw` should be used to avoid escaping `\`. (`javascript:S7780`)
- **Line 139:** [MINOR] Unexpected negated condition. (`javascript:S7735`)
- **Line 161:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

### app/static/js/ui.js (12 issues)

- **Line 4:** [MINOR] Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 40:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 40:** [MAJOR] Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 40:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 43:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 49:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 50:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 72:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 77:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 89:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 99:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 102:** [MINOR] Prefer `globalThis` over `window`. (`javascript:S7764`)

