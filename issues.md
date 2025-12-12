# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 23

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

### 🔵 MINOR Issues (23)

#### app/static/js/HeaderAuth.js
- **Line 130:** Prefer `globalThis` over `window`. (`javascript:S7764`)

#### app/static/js/InfiniteFeed.js
- **Line 194:** Prefer `Number.parseInt` over `parseInt`. (`javascript:S7773`)

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

---

## Summary by Priority

1. **🔴 CRITICAL (25 issues)** - Address immediately: Complex functions need refactoring
2. **🟠 BLOCKER (5 issues)** - Fix next: Missing variable declarations
3. **🟡 MAJOR (95 issues)** - Schedule soon: Code quality improvements
4. **🔵 MINOR (88 issues)** - Address gradually: Style and best practice improvements

## All Issues (213)

### JavaScript Issues (67)

