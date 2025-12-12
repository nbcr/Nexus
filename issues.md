# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 46

**JavaScript Issues:** 45

## Issues by Severity

### 🔴 CRITICAL Issues (0)

*All CRITICAL issues have been resolved.*

---

### 🟠 BLOCKER Issues (0)

*All BLOCKER issues have been resolved.*

---

### 🟡 MAJOR Issues (0)

*All MAJOR issues have been resolved.*

---

---

### 🔵 MINOR Issues (88)

#### app/core/input_validation.py
- **Line 293:** Use concise character class syntax '\w' instead of '[a-zA-Z0-9_]'. (`python:S6353`)

#### app/core/secure_request_handler.py
- **Line 131:** Remove the unused local variable "e". (`python:S1481`)
- **Line 193:** Remove the unused local variable "safe_error". (`python:S1481`)

#### app/middleware/security_middleware.py
- **Line 76:** Use asynchronous features in this function or remove the `async` keyword. (`python:S7503`)

#### app/static/js/HeaderAuth.js
- **Line 130:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/InfiniteFeed.js
- **Line 194:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)

#### app/static/js/feed-notifier.js
- **Line 26:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 29:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 121:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 124:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 154:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 156:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 12:** Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 239:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 240:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 244:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/header.js
- **Line 409:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 426:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 517:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 136:** Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 146:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 182:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 24:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 27:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 47:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 49:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/history-tracker.js
- **Line 8:** Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 83:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 226:** Prefer `globalThis` over `window`. (`javascript:S7764`)

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
- **Line 52:** Don't use a zero fraction in the number. (`javascript:S7748`)
- **Line 275:** Prefer `.at(…)` over `[….length - index]`. (`javascript:S7755`)

#### app/static/js/trending.js
- **Line 20:** Unexpected negated condition. (`javascript:S7735`)
- **Line 86:** Remove the declaration of the unused 'trendsHtml' variable. (`javascript:S1481`)
- **Line 96:** `String.raw` should be used to avoid escaping `\`. (`javascript:S7780`)
- **Line 161:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 139:** Unexpected negated condition. (`javascript:S7735`)

#### app/static/js/ui.js
- **Line 4:** Prefer class field declaration over `this` assignment in constructor for static values. (`javascript:S7757`)
- **Line 40:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 40:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 43:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 49:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 50:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 72:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 77:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 89:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 99:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 102:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/templates/base.html
- **Line 11:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 11:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/templates/forgot-password.html
- **Line 68:** Handle this exception or don't catch it at all. (`javascript:S2486`)

#### app/templates/history.html
- **Line 422:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)
- **Line 507:** Unexpected negated condition. (`javascript:S7735`)

#### app/templates/index.html
- **Line 68:** Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 105:** Add an "alt" attribute to this image. (`Web:ImgWithoutAltCheck`)

#### app/templates/logged-out.html
- **Line 83:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/templates/login.html
- **Line 67:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 74:** Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 93:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 99:** Remove the declaration of the unused 'password' variable. (`javascript:S1481`)
- **Line 196:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 206:** Handle this exception or don't catch it at all. (`javascript:S2486`)

#### app/templates/register.html
- **Line 136:** Prefer `String#replaceAll()` over `String#replace()`. (`javascript:S7781`)
- **Line 68:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 186:** arrow function is equivalent to `Boolean`. Use `Boolean` directly. (`javascript:S7770`)
- **Line 234:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 245:** Handle this exception or don't catch it at all. (`javascript:S2486`)

#### app/templates/reset-password.html
- **Line 35:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 101:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 110:** Handle this exception or don't catch it at all. (`javascript:S2486`)

#### app/templates/settings.html
- **Line 321:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### load_data.py
- **Line 49:** Remove the unused local variable "feed_name". (`python:S1481`)

#### scripts/update_cache_bust.py
- **Line 131:** Remove the unused local variable "css_files". (`python:S1481`)
- **Line 132:** Remove the unused local variable "js_files". (`python:S1481`)

#### storage_monitor.py
- **Line 144:** Remove the unused local variable "db_growth_per_day". (`python:S1481`)

#### test_fetch_performance.py
- **Line 21:** Remove the unused local variable "original_limit". (`python:S1481`)
- **Line 24:** Remove the unused local variable "fetcher". (`python:S1481`)

#### test_russian_attacks.py
- **Line 49:** Replace the unused loop index "i" with "_". (`python:S1481`)

---

## Summary by Priority

1. **🔴 CRITICAL (25 issues)** - Address immediately: Complex functions need refactoring
2. **🟠 BLOCKER (5 issues)** - Fix next: Missing variable declarations
3. **🟡 MAJOR (95 issues)** - Schedule soon: Code quality improvements
4. **🔵 MINOR (88 issues)** - Address gradually: Style and best practice improvements

## All Issues (213)

### JavaScript Issues (67)

