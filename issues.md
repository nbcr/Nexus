# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 49

**JavaScript Issues:** 40

## Issues by Severity

### 🟠 CRITICAL Issues (1)

#### app/static/js/header.js
- **Line 206:** Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. (`javascript:S3776`)

---

### 🟡 MAJOR Issues (8)

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

---

### 🔵 MINOR Issues (40)

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
- **Line 24:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 27:** '(from: number, length?: number): string' is deprecated. (`javascript:S1874`)
- **Line 41:** Use the "RegExp.exec()" method instead. (`javascript:S6594`)
- **Line 118:** Handle this exception or don't catch it at all. (`javascript:S2486`)
- **Line 129:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 165:** Prefer `globalThis` over `window`. (`javascript:S7764`)
- **Line 371:** Remove the declaration of the unused 'lastScrollTop' variable. (`javascript:S1481`)
- **Line 393:** Prefer `globalThis` over `window`. (`javascript:S7764`)

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
- **Line 136:** Unexpected negated condition. (`javascript:S7735`)
- **Line 158:** Prefer `globalThis` over `window`. (`javascript:S7764`)

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

---

## Summary by Priority

**🟠 CRITICAL (1 issue)** - Address immediately
**🟡 MAJOR (8 issues)** - Schedule soon
**🔵 MINOR (40 issues)** - Address gradually
**Total: 49 issues**

