# SonarQube Issues Report

**Project:** nbcr_Nexus

**Total Issues:** 11

**JavaScript Issues:** 1

## Issues by Severity

### 🟠 CRITICAL Issues (1)

#### scripts/get_security_hotspots.py
- **Line 108:** Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed. (`python:S3776`)

---

### 🟡 MAJOR Issues (7)

#### app/static/css/admin.css
- **Line 407:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 510:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### app/templates/history.html
- **Line 198:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 187:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)
- **Line 194:** Text does not meet the minimal contrast requirement with its background. (`css:S7924`)

#### db_setup.sh
- **Line 88:** Redirect this error message to stderr (>&2). (`shelldre:S7677`)

#### scripts/get_security_hotspots.py
- **Line 41:** Add replacement fields or use a normal string instead of an f-string. (`python:S3457`)

---

### 🔵 MINOR Issues (1)

#### app/static/js/history-tracker.js
- **Line 227:** Prefer `globalThis` over `window`. (`javascript:S7764`)

---

### ⚪ INFO Issues (2)

#### app/api/v1/routes/settings.py
- **Line 30:** Complete the task associated to this "TODO" comment. (`python:S1135`)

#### app/services/content_recommendation.py
- **Line 230:** Complete the task associated to this "TODO" comment. (`python:S1135`)

---

## Summary by Priority

**🟠 CRITICAL (1 issues)** - Address immediately: Complex functions need refactoring
**🟡 MAJOR (7 issues)** - Schedule soon: Code quality improvements
**🔵 MINOR (1 issues)** - Address gradually: Style and best practice improvements
**⚪ INFO (2 issues)** - Optional: Informational suggestions

## All Issues (11)

### JavaScript Issues (1)

