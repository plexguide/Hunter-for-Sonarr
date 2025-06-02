# Huntarr Development Guidelines

Quick reference for development patterns, common issues, and critical requirements.

## 🚨 CRITICAL RULES

### 🚫 NO AUTO-COMMITTING
**NEVER automatically commit changes without explicit user approval.**
- Present fixes to user first
- Get explicit approval before committing  
- Let user decide when to commit

### 🔄 MANDATORY TESTING WORKFLOW
```bash
# ALWAYS rebuild and test changes
cd /Users/home/Huntarr/Huntarr.io && docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build

# Check logs for errors
docker logs huntarr
```

### 🌐 CROSS-PLATFORM REQUIREMENTS
- **NEVER use hard-coded absolute paths** (e.g., `/config/file.json`)
- **ALWAYS use `os.path.join()`** for path construction
- **ALWAYS use relative URLs** in frontend (e.g., `./api/` not `/api/`)
- **ALWAYS test**: Docker, Windows, Mac, Linux, subpaths (`domain.com/huntarr/`)

## 🐛 COMMON ISSUE PATTERNS

### 1. Frontend Log Regex Issues
**Symptoms:** Logs generated but not displayed for specific apps
**Root Cause:** Malformed regex with double backslashes
**Fix:**
```javascript
// ❌ BROKEN
const logRegex = /^(?:\\[(\\w+)\\]\\s)?([\\d\\-]+\\s[\\d:]+)\\s-\\s([\\w\\.]+)\\s-\\s(\\w+)\\s-\\s(.*)$/;

// ✅ FIXED  
const logRegex = /^(?:\[(\w+)\]\s)?([^\s]+\s[^\s]+)\s-\s([\w\.]+)\s-\s(\w+)\s-\s(.*)$/;
```
**File:** `/frontend/static/js/new-main.js` - `connectEventSource()` method

### 2. DEBUG Log Filtering Race Condition
**Symptoms:** DEBUG logs appear in wrong filters (Info, Warning, Error)
**Root Cause:** EventSource adds logs without checking current filter
**Fix:** Apply filter to new entries as they arrive
```javascript
// In EventSource onmessage handler, after appendChild:
const currentLogLevel = this.elements.logLevelSelect ? this.elements.logLevelSelect.value : 'all';
if (currentLogLevel !== 'all') {
    this.applyFilterToSingleEntry(logEntry, currentLogLevel);
}
```
**File:** `/frontend/static/js/new-main.js` - `connectEventSource()` method

### 3. Hard-Coded Path Issues
**Symptoms:** "Error Loading" on bare metal, works in Docker
**Root Cause:** Hard-coded Docker paths don't exist on bare metal
**Fix:** Environment detection pattern
```python
def _detect_environment():
    return os.path.exists('/config') and os.path.exists('/app')

def _get_paths():
    if _detect_environment():
        return {'data': '/config/tally/sleep.json'}
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return {'data': os.path.join(base_dir, 'data', 'tally', 'sleep.json')}
```

### 4. JavaScript Variable Undefined Errors
**Symptoms:** `ReferenceError: variableName is not defined` in settings
**Root Cause:** Missing variable declarations in form generation
**Fix:** Ensure all variables are declared before use
```javascript
generateAppForm: function(container, settings = {}) {
    let instancesHtml = `...`;
    let searchSettingsHtml = `...`;  // CRITICAL - must declare
    container.innerHTML = instancesHtml + searchSettingsHtml;
}
```
**File:** `/frontend/static/js/settings_forms.js`

### 5. Subpath Compatibility Breaks
**Symptoms:** Works at root domain but fails in subdirectories
**Root Cause:** Absolute URLs in JavaScript/templates
**Fix:** Use relative URLs everywhere
```javascript
// ❌ BROKEN
window.location.href = '/';
fetch('/api/endpoint');

// ✅ FIXED
window.location.href = './';
fetch('./api/endpoint');
```

## 🔧 DEVELOPMENT WORKFLOW

### Before Any Changes
- [ ] Check current working directory: `/Users/home/Huntarr/Huntarr.io`
- [ ] Ensure you're on correct branch
- [ ] Review .github/listen.md for latest patterns

### Making Changes
- [ ] Edit source code (never modify inside container)
- [ ] Rebuild: `docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build`
- [ ] Check logs: `docker logs huntarr`
- [ ] Test functionality

### Before Committing
- [ ] Test in Docker environment
- [ ] Test cross-platform compatibility
- [ ] Test subpath scenarios (`domain.com/huntarr/`)
- [ ] Check browser console for errors
- [ ] Get user approval before committing

### Path Hunting Commands
```bash
# Search for hard-coded paths
grep -r "/config" src/ --include="*.py"
grep -r "/app" src/ --include="*.py"
grep -r "href=\"/" frontend/
grep -r "window.location.href = '/" frontend/
```

## 📁 KEY FILE LOCATIONS

### Backend Core
- `/src/routes.py` - API endpoints
- `/src/primary/cycle_tracker.py` - Timer functionality
- `/src/primary/utils/logger.py` - Logging configuration
- `/src/primary/settings_manager.py` - Settings handling

### Frontend Core  
- `/frontend/static/js/new-main.js` - Main UI logic
- `/frontend/static/js/settings_forms.js` - Settings forms
- `/frontend/templates/components/` - UI components

### Critical Files for Cross-Platform
- `/src/primary/utils/config_paths.py` - Path utilities
- `/src/primary/cycle_tracker.py` - Timer paths
- Any `*_routes.py` files

## 🎯 DEBUGGING QUICK REFERENCE

### Log Issues
1. Check if logs exist: `docker exec huntarr cat /config/logs/[app].log`
2. Test backend streaming: `curl -N -s "http://localhost:9705/logs?app=[app]"`
3. Check browser console for JavaScript errors
4. Verify regex patterns in `new-main.js`

### Path Issues
1. Check environment detection logic
2. Verify paths exist in target environment
3. Test with both Docker and bare metal
4. Check file permissions

### JavaScript Issues
1. Check browser console for errors
2. Search for undefined variables: `grep -r "variableName" frontend/`
3. Verify HTML structure matches selectors
4. Compare with working functions

### Settings Issues
1. Check form generation functions
2. Verify `getFormSettings()` method
3. Test save/load cycle
4. Check API endpoints

## ⚠️ ANTI-PATTERNS TO AVOID

1. **❌ Hard-coded absolute paths:** `/config/file.json`
2. **❌ Absolute URLs in frontend:** `/api/endpoint`, `window.location.href = '/'`
3. **❌ Modifying files inside containers**
4. **❌ Creating temporary/helper files instead of fixing source**
5. **❌ Auto-committing without approval**
6. **❌ Double backslashes in regex patterns**
7. **❌ Testing only in Docker (must test bare metal)**
8. **❌ Adding to main CSS/JS files (create separate files)**

## 🚀 ENVIRONMENT DETECTION PATTERN

Use this pattern for all cross-platform file operations:

```python
import os

def _detect_environment():
    """Detect if running in Docker or bare metal"""
    return os.path.exists('/config') and os.path.exists('/app')

def _get_cross_platform_path(relative_path):
    """Get appropriate path based on environment"""
    if _detect_environment():
        # Docker environment
        return os.path.join('/config', relative_path)
    else:
        # Bare metal environment  
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, 'data', relative_path)
```

## 📝 MEMORY GUIDELINES

**Create memories for:**
- ✅ Bug fixes with root cause analysis
- ✅ New features
- ✅ Cross-platform compatibility fixes
- ✅ Performance improvements

**Format:**
```
Title: Brief description
Content: Root cause, files modified, solution approach, testing notes
Tags: ["bug_fix", "feature", "frontend", "backend"]
```

---

*Quick reference for Huntarr development. Update when new patterns are discovered.*
