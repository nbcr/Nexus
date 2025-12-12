# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 191

**JavaScript Issues:** 58

## Issues by Severity

### 🔴 CRITICAL Issues (13)



#### app/core/input_validation.py
- **Line 281:** Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. (`python:S3776`)

#### app/core/secure_request_handler.py
- **Line 15:** Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed. (`python:S3776`)

#### app/static/js/HeaderDarkMode.js
- **Line 45:** Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)



#### app/templates/register.html
- **Line 170:** Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. (`javascript:S3776`)



#### block_china_russia.py
- **Line 127:** Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed. (`python:S3776`)





#### scripts/check_categorization.py
- **Line 68:** Specify an exception class to catch or reraise the exception (`python:S5754`)



#### scripts/update_cache_bust.py
- **Line 119:** Refactor this function to reduce its Cognitive Complexity from 25 to the 15 allowed. (`python:S3776`)



#### test_fetch_performance.py
- **Line 51:** Refactor this function to reduce its Cognitive Complexity from 24 to the 15 allowed. (`python:S3776`)

#### update_existing_topics.py
- **Line 15:** Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed. (`python:S3776`)

---

### 🟠 BLOCKER Issues (0)

*All BLOCKER issues have been resolved.*

---

### 🟡 MAJOR Issues (95)



#### app/api/v1/routes/settings.py
- **Line 30:** Take the required action to fix the issue indicated by this "FIXME" comment. (`python:S1134`)

#### app/services/content_recommendation.py
- **Line 230:** Take the required action to fix the issue indicated by this "FIXME" comment. (`python:S1134`)

#### app/static/css/admin.css
- **Line 407:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 510:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/css/auth.css
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
- **Line 191:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/static/css/trending.css
- **Line 225:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 50:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 114:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)



#### app/static/js/HeaderAuth.js
- **Line 175:** Promise-returning function provided to variable where a void return was expected. (`javascript:S6544`)

#### app/static/js/HoverTracker.js
- **Line 389:** 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)



#### app/static/js/hover-tracker.js
- **Line 399:** 'If' statement should not be the only statement in 'else' block (`javascript:S6660`)





#### app/templates/admin.html
- **Line 244:** A form label must be associated with a control. (`Web:S6853`)

#### app/templates/history.html
- **Line 187:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 194:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 413:** Extract this nested ternary operation into an independent statement. (`javascript:S3358`)
- **Line 566:** Prefer top-level await over an async function `loadHistory` call. (`javascript:S7785`)

#### app/templates/index.html
- **Line 98:** Headings must have content and the content must be accessible by a screen reader. (`Web:S6850`)

#### app/templates/login.html
- **Line 41:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)
- **Line 51:** Move function 'getCookie' to the outer scope. (`javascript:S7721`)
- **Line 81:** Prefer top-level await over an async function `checkAuthAndRedirect` call. (`javascript:S7785`)
- **Line 99:** Remove this useless assignment to variable "password". (`javascript:S1854`)

#### app/templates/register.html
- **Line 98:** Unnecessary escape character: \[. (`javascript:S6535`)
- **Line 98:** Unnecessary escape character: \/. (`javascript:S6535`)
- **Line 134:** Move function 'summarizeErrorMessage' to the outer scope. (`javascript:S7721`)

#### benchmark_feeds.py
- **Line 189:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### check_logs_folder.sh
- **Line 5:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)
- **Line 13:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)

#### create_admin.py
- **Line 65:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 36:** Wrap this call to input() with await asyncio.to_thread(input). (`python:S7501`)
- **Line 36:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 58:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 64:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 67:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### db_setup.sh
- **Line 88:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

#### fix_database_url.sh
- **Line 6:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)
- **Line 7:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

#### fix_env.sh
- **Line 6:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)

#### get_db_stats.sh
- **Line 4:** Add an explicit return statement at the end of the function. (`shelldre:S7682`)
- **Line 5:** Assign this positional parameter to a local variable. (`shelldre:S7679`)

#### intrusion_detector.py
- **Line 180:** Remove the unused function parameter "url". (`python:S1172`)

#### nginx/404.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### nginx/500.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### nginx/502.html
- **Line 67:** Non-interactive elements should not be assigned mouse or keyboard event listeners. (`Web:S6847`)

#### restart-nginx.sh
- **Line 9:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)

#### run_migration.sh
- **Line 7:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)
- **Line 13:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)

#### scripts/backup_with_storage_check.py
- **Line 100:** Return a value of type "dict" instead of "NoneType" or update function "get_filesystem_usage" type hint. (`python:S5886`)

#### scripts/check_categorization.py
- **Line 297:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 303:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### scripts/fetch_content.py
- **Line 23:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 26:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### scripts/get_sonar_issues.py
- **Line 93:** Remove the unused function parameter "feedrenderer_issues". (`python:S1172`)
- **Line 95:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 197:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 198:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### scripts/remove_google_trends.py
- **Line 85:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### scripts/test_backup_restore.sh
- **Line 12:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)
- **Line 45:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

#### storage_monitor.py
- **Line 400:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 421:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### test_betakit.py
- **Line 38:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 43:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### test_fetch_performance.py
- **Line 70:** Add a parameter to function "patched_process" and use variable "items_limit" as its default value;The value of "items_limit" might change at the next loop iteration. (`python:S1515`)
- **Line 113:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 122:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### test_ids.py
- **Line 56:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 106:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 110:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 118:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### test_instant_block.py
- **Line 17:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)
- **Line 19:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

#### update_service.sh
- **Line 5:** Use '[[' instead of '[' for conditional tests. The '[[' construct is safer and more feature-rich. (`shelldre:S7688`)
- **Line 9:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)
- **Line 15:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

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

