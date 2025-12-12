# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 58

**JavaScript Issues:** 22

## Issues by Severity

### 🟠 CRITICAL Issues (1)

#### app/static/js/header.js
- **Line 282:** Remove this use of the "void" operator. (`javascript:S3735`)

---

### 🟡 MAJOR Issues (33)

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

#### app/static/js/hover-tracker.js
- **Line 399:** 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)

#### app/templates/admin.html
- **Line 244:** A form label must be associated with a control. (`Web:S6853`)

#### app/templates/history.html
- **Line 579:** Prefer top-level await over an async function `initHistory` call. (`javascript:S7785`)
- **Line 187:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 194:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/utils/async_rss_parser.py
- **Line 83:** Remove the unused function parameter "feed_url". (`python:S1172`)
- **Line 92:** Return a value of type "dict" instead of "NoneType" or update function "_extract_json_entries" type hint. (`python:S5886`)

#### db_setup.sh
- **Line 88:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

#### nginx/404.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### nginx/500.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### nginx/502.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

---

### 🔵 MINOR Issues (22)

#### app/static/js/header.js
- **Line 407:** Prefer `globalThis` over `window`. (`javascript:S7764`)
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

#### app/templates/history.html
- **Line 504:** Use the opposite operator (<=) instead. (`javascript:S1940`)
- **Line 516:** Unexpected negated condition. (`javascript:S7735`)

#### geoip_checker.py
- **Line 97:** Remove the unused local variable "e". (`python:S1481`)

---

### ⚪ INFO Issues (2)

#### app/api/v1/routes/settings.py
- **Line 30:** Complete the task associated to this "TODO" comment. (`python:S1135`)

#### app/services/content_recommendation.py
- **Line 230:** Complete the task associated to this "TODO" comment. (`python:S1135`)

---

## Summary by Priority

**🟠 CRITICAL (1 issues)** - Address immediately: Complex functions need refactoring
**🟡 MAJOR (33 issues)** - Schedule soon: Code quality improvements
**🔵 MINOR (22 issues)** - Address gradually: Style and best practice improvements
**⚪ INFO (2 issues)** - Optional: Informational suggestions

## All Issues (58)

### JavaScript Issues (22)

