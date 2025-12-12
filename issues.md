# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 116

**JavaScript Issues:** 49

## Issues by Severity

### 🟠 CRITICAL Issues (6)

#### alembic/env.py
- **Line 27:** Import only needed names or import the module and then use its members. (`python:S2208`)

#### app/static/js/header.js
- **Line 206:** Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)

#### app/utils/async_rss_parser.py
- **Line 83:** Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. (`python:S3776`)

#### block_china_russia.py
- **Line 133:** Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. (`python:S3776`)

#### nexus_service.py
- **Line 268:** Refactor this function to reduce its Cognitive Complexity from 23 to the 15 allowed. (`python:S3776`)

#### test_fetch_performance.py
- **Line 46:** Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed. (`python:S3776`)

---

### 🟡 MAJOR Issues (52)

#### add_content_fields.sql
- **Line 16:** Remove this commented out code. (`plsql:S125`)

#### app/core/input_validation.py
- **Line 203:** Return a value of type "int" instead of "NoneType" or update function "_parse_id_string" type hint. (`python:S5886`)

#### app/static/css/admin.css
- **Line 407:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 510:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/css/auth.css
- **Line 382:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 297:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/css/components.css
- **Line 354:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 390:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 132:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 137:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 142:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 50:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 68:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 77:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 87:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 118:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 125:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 150:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 294:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/css/feed.css
- **Line 361:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/css/trending.css
- **Line 225:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 50:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 114:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/js/FeedRenderer.js
- **Line 48:** Prefer using an optional chain expression instead, as it's more concise and easier to read. (`javascript:S6582`)
- **Line 124:** Refactor this code to not use nested template literals. (`javascript:S4624`)

#### app/static/js/HeaderAuth.js
- **Line 175:** Promise-returning function provided to variable where a void return was expected. (`javascript:S6544`)

#### app/static/js/HoverTracker.js
- **Line 389:** 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)

#### app/static/js/header.js
- **Line 265:** Expected an assignment or function call and instead saw an expression. (`javascript:S905`)
- **Line 386:** Remove this commented out code. (`javascript:S125`)

#### app/static/js/hover-tracker.js
- **Line 399:** 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)

#### app/templates/admin.html
- **Line 244:** A form label must be associated with a control. (`Web:S6853`)

#### app/templates/history.html
- **Line 579:** Prefer top-level await over an async function `initHistory` call. (`javascript:S7785`)
- **Line 187:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 194:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/templates/index.html
- **Line 107:** Remove redundant word "image" from the "alt" attribute of your "img" tag. (`Web:S6851`)

#### app/templates/login.html
- **Line 81:** Prefer top-level await over an async IIFE. (`javascript:S7785`)
- **Line 164:** Expected an assignment or function call and instead saw an expression. (`javascript:S905`)
- **Line 51:** Move function 'getCookie' to the outer scope. (`javascript:S7721`)
- **Line 101:** Remove this useless assignment to variable "password". (`javascript:S1854`)

#### app/templates/register.html
- **Line 167:** Move function 'clearFormErrors' to the outer scope. (`javascript:S7721`)
- **Line 173:** Move function 'validatePasswordReqs' to the outer scope. (`javascript:S7721`)
- **Line 201:** Move function 'handleErrorResponse' to the outer scope. (`javascript:S7721`)
- **Line 94:** Unnecessary escape character: \[. (`javascript:S6535`)
- **Line 130:** Move function 'summarizeErrorMessage' to the outer scope. (`javascript:S7721`)

#### benchmark_feeds.py
- **Line 189:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### db_setup.sh
- **Line 88:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

#### intrusion_detector.py
- **Line 180:** Remove the unused function parameter "url". (`python:S1172`)

#### nginx/404.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### nginx/500.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### nginx/502.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### scripts/get_sonar_issues.py
- **Line 151:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### storage_monitor.py
- **Line 399:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

---

### 🔵 MINOR Issues (53)

#### app/static/js/HeaderAuth.js
- **Line 39:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 166:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/feed-notifier.js
- **Line 158:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 160:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 243:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 244:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 248:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/header.js
- **Line 371:** Remove the declaration of the unused 'lastScrollTop' variable. (`javascript:S1481`)
- **Line 393:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 118:** Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 129:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 165:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 24:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 27:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 41:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)

#### app/static/js/history-tracker.js
- **Line 227:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/hover-tracker.js
- **Line 127:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 157:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 168:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 182:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 191:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 290:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 307:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 363:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 395:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 399:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 404:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/trending.js
- **Line 20:** Unexpected negated condition. (`javascript:S7735`)
- **Line 93:** `String.raw` should be used to avoid escaping `\`. (`javascript:S7780`)
- **Line 158:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 136:** Unexpected negated condition. (`javascript:S7735`)

#### app/static/js/ui.js
- **Line 5:** Useless constructor. (`javascript:S6647`)
- **Line 41:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 44:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 50:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 51:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 73:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 78:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 90:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 100:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 103:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/templates/history.html
- **Line 504:** Use the opposite operator (<=) instead. (`javascript:S1940`)
- **Line 516:** Unexpected negated condition. (`javascript:S7735`)

#### app/templates/login.html
- **Line 74:** Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 101:** Remove the declaration of the unused 'password' variable. (`javascript:S1481`)

#### app/templates/register.html
- **Line 132:** Prefer `String#replaceAll()` over `String#replace()`. (`javascript:S7781`)
- **Line 175:** arrow function is equivalent to `Boolean`. Use `Boolean` directly. (`javascript:S7770`)
- **Line 198:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### geoip_checker.py
- **Line 97:** Remove the unused local variable "e". (`python:S1481`)

#### scripts/get_sonar_issues.py
- **Line 29:** Remove the unused local variable "e". (`python:S1481`)

#### storage_monitor.py
- **Line 195:** Remove the unused local variable "e". (`python:S1481`)
- **Line 236:** Remove the unused local variable "e". (`python:S1481`)
- **Line 279:** Remove the unused local variable "e". (`python:S1481`)

---

### ⚪ INFO Issues (2)

#### app/api/v1/routes/settings.py
- **Line 30:** Complete the task associated to this "TODO" comment. (`python:S1135`)

#### app/services/content_recommendation.py
- **Line 230:** Complete the task associated to this "TODO" comment. (`python:S1135`)

---

## Summary by Priority

**🟠 CRITICAL (6 issues)** - Address immediately: Complex functions need refactoring
**🟡 MAJOR (52 issues)** - Schedule soon: Code quality improvements
**🔵 MINOR (53 issues)** - Address gradually: Style and best practice improvements
**⚪ INFO (2 issues)** - Optional: Informational suggestions

## All Issues (116)

### JavaScript Issues (49)

