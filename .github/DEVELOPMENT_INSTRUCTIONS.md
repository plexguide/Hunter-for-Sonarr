# Huntarr Development Instructions

This document serves as a constant reminder and reference for common development tasks, debugging procedures, and fix patterns in the Huntarr codebase.

## 🚀 Version Update Workflow

**When making changes:**
1. Update `/version.txt` with new version number
2. **ALWAYS rebuild and test with this command:**
   ```bash
   cd /Users/home/Huntarr/Huntarr.io && docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build
   ```
3. **Check logs for errors related to your changes:**
   ```bash
   docker logs huntarr
   ```
4. **Test cross-platform compatibility** (Windows, Mac, Docker, Linux bare metal)
5. **Test subpath reverse proxy scenarios** (e.g., `/huntarr/` prefix)
6. Create memory entry for significant fixes

## 🐛 Common Issue Patterns & Solutions

### 1. Timer Loading Errors ("Error Loading" on Dashboard)

**Symptoms:**
- Countdown timers show "Error Loading" 
- Occurs on bare metal installations
- Works fine in Docker

**Root Cause:**
- Hard-coded Docker paths (`/config/tally/sleep.json`) don't exist on bare metal

**Fix Pattern:**
```python
# In cycle_tracker.py - Add environment detection
def _detect_environment():
    """Detect if we're running in Docker or bare metal environment"""
    return os.path.exists('/config') and os.path.exists('/app')

def _get_paths():
    """Get appropriate paths based on environment"""
    if _detect_environment():
        # Docker environment
        return {
            'sleep_data': '/config/tally/sleep.json',
            'cycle_data': '/config/settings/cycle_data.json'
        }
    else:
        # Bare metal environment
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return {
            'sleep_data': os.path.join(base_dir, 'data', 'tally', 'sleep.json'),
            'cycle_data': os.path.join(base_dir, 'data', 'settings', 'cycle_data.json')
        }
```

**Files to Check:**
- `/src/primary/cycle_tracker.py` - Path constants
- `/src/routes.py` - API error handling

### 2. JavaScript "Variable Not Defined" Errors in Settings

**Symptoms:**
- Error: `ReferenceError: searchSettingsHtml is not defined`
- Settings page fails to load for specific apps

**Root Cause:**
- Missing variable declarations in settings form generation functions

**Fix Pattern:**
```javascript
// In settings_forms.js - Each app form needs this pattern:
generateAppForm: function(container, settings = {}) {
    // 1. Create instancesHtml variable
    let instancesHtml = `...`;
    
    // 2. Create searchSettingsHtml variable (CRITICAL!)
    let searchSettingsHtml = `...`;
    
    // 3. Combine them
    container.innerHTML = instancesHtml + searchSettingsHtml;
}
```

**Files to Check:**
- `/frontend/static/js/settings_forms.js` - All `generate*Form` functions

### 3. Settings Save Issues

**Symptoms:**
- Settings appear to save but don't persist
- "Save successful" message but values reset

**Root Cause:**
- `getFormSettings()` method doesn't handle specific app types properly

**Fix Pattern:**
```javascript
// In new-main.js - Add special case handling
getFormSettings: function() {
    // Special handling for general settings
    if (app === 'general') {
        // Collect all form inputs specifically
        // Handle special fields like apprise_urls
    }
    // Handle other app types...
}
```

**Files to Check:**
- `/frontend/static/js/new-main.js` - `getFormSettings()` method
- `/frontend/static/js/settings_forms.js` - Form generation

### 4. UI Element Visibility Issues

**Symptoms:**
- Buttons cut off at bottom of screen
- Elements not visible on small screens
- Browser-specific rendering issues

**Fix Pattern:**
```css
/* Add proper positioning and safe areas */
.element {
    position: fixed;
    bottom: 0;
    padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
    z-index: 1000;
    background: rgba(0,0,0,0.8);
    backdrop-filter: blur(10px);
}

/* Firefox-specific fixes */
@-moz-document url-prefix() {
    .element {
        /* Firefox-specific styles */
    }
}
```

**Files to Check:**
- Template files in `/frontend/templates/components/`
- CSS in template `<style>` sections

## 🔍 Hard-Coded Path Detection & Systematic Hunting

**LESSON LEARNED:** Even after fixing some hard-coded paths, others can remain hidden and cause cross-platform issues. Use this systematic approach:

### Step 1: Comprehensive Path Search
```bash
# Search for ALL potential hard-coded path patterns
grep -r "/config" src/ --include="*.py"
grep -r "/app" src/ --include="*.py" 
grep -r "/data" src/ --include="*.py"
grep -r "/tmp" src/ --include="*.py"
grep -r "C:\\" src/ --include="*.py"
```

### Step 2: Validate Each Result
For each result, determine if it's:
- ✅ **Legitimate:** Comments, environment detection logic, or Flask routes
- ❌ **Problem:** Actual file/directory paths that should use `config_paths.py`

### Step 3: Priority File Checklist
**CRITICAL FILES** that commonly contain hard-coded paths:
- [ ] `cycle_tracker.py` - Timer functionality (HIGH IMPACT)
- [ ] `history_manager.py` - Data storage
- [ ] `web_server.py` - Cache directories
- [ ] `settings_manager.py` - Configuration files
- [ ] Any app-specific routes (`*_routes.py`)

### Step 4: Fix Pattern
Replace hard-coded paths with centralized utilities:

**❌ WRONG:**
```python
CACHE_DIR = '/config/settings/sponsor'
data_path = '/config/tally/sleep.json'
```

**✅ CORRECT:**
```python
from src.primary.utils.config_paths import get_path
CACHE_DIR = get_path('settings', 'sponsor')
data_path = get_path('tally', 'sleep.json')
```

### Step 5: Post-Fix Verification
1. Update `version.txt`
2. Rebuild: `docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build`
3. Check logs: `docker logs huntarr`
4. Verify path resolution in logs shows correct environment detection

## 🌐 Cross-Platform Compatibility Requirements

**CRITICAL: All paths must work on Windows, Docker, and Mac with subpaths**

### Path Handling Rules:
1. **NEVER use hard-coded absolute paths** (e.g., `/config/file.json`)
2. **ALWAYS use `os.path.join()`** for cross-platform compatibility
3. **ALWAYS use relative paths from project root** when possible
4. **Support reverse proxy subpaths** (e.g., `domain.com/huntarr/`)

### Environment Detection Pattern:
```python
import os

def _detect_environment():
    """Detect if we're running in Docker or bare metal environment"""
    return os.path.exists('/config') and os.path.exists('/app')

def _get_cross_platform_paths():
    """Get appropriate paths based on environment - CROSS-PLATFORM SAFE"""
    if _detect_environment():
        # Docker environment (Linux containers)
        return {
            'sleep_data': os.path.join('/config', 'tally', 'sleep.json'),
            'cycle_data': os.path.join('/config', 'settings', 'cycle_data.json'),
            'web_accessible': '/config/tally/'  # For web serving
        }
    else:
        # Bare metal environment (Windows/Mac/Linux)
        # Get project root dynamically
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(project_root, 'data')
        
        return {
            'sleep_data': os.path.join(data_dir, 'tally', 'sleep.json'),
            'cycle_data': os.path.join(data_dir, 'settings', 'cycle_data.json'),
            'web_accessible': os.path.join(data_dir, 'tally')  # For web serving
        }
```

### Subpath Support Pattern:
```python
# For web routes - support reverse proxy subpaths
@app.route('/api/sleep.json', methods=['GET'])
@app.route('/<path:subpath>/api/sleep.json', methods=['GET'])  # Subpath support
def api_get_sleep_json(subpath=None):
    """Serve sleep.json with subpath support"""
    # Handle both direct and subpath access
    pass
```

### Frontend URL Pattern:
```javascript
// ALWAYS use relative URLs for API calls to support subpaths
function fetchData() {
    // ✅ GOOD - Works with subpaths
    fetch('./api/sleep.json')
    
    // ❌ BAD - Breaks with subpaths
    fetch('/api/sleep.json')
}
```

## 🔧 Development Workflows

### Environment Testing Checklist

**Before marking issue as resolved:**
- [ ] Test in Docker environment
- [ ] Test on Linux bare metal
- [ ] Test on Windows bare metal  
- [ ] Test on macOS bare metal
- [ ] Verify API endpoints work
- [ ] Check browser console for errors
- [ ] Test with different screen sizes

### Debugging JavaScript Issues

1. **Check browser console** for error messages
2. **Search for undefined variables** in codebase:
   ```bash
   grep -r "variableName" frontend/static/js/
   ```
3. **Compare with working functions** in same file
4. **Verify HTML structure** matches JavaScript selectors

### Debugging Path Issues

1. **Check if paths exist** in target environment
2. **Verify environment detection** logic
3. **Test with both absolute and relative paths**
4. **Check file permissions** on bare metal

### Memory Creation Guidelines

**Create memories for:**
- ✅ Legitimate bug fixes with root cause analysis
- ✅ New feature implementations
- ✅ Configuration changes that affect user experience
- ✅ Cross-platform compatibility fixes

**Memory format:**
```
Title: Brief description of what was fixed/implemented
Content: 
- Root cause analysis
- Files modified
- Solution approach
- Testing notes
Tags: ["bug_fix", "feature", "frontend", "backend", etc.]
```

## 📁 Key File Locations

### Backend Files
- `/src/routes.py` - API endpoints
- `/src/primary/cycle_tracker.py` - Timer and cycle management
- `/src/primary/` - Core application logic

### Frontend Files
- `/frontend/static/js/settings_forms.js` - Settings page forms
- `/frontend/static/js/new-main.js` - Main UI logic
- `/frontend/templates/components/` - UI components

### Configuration Files
- `/version.txt` - Application version
- `/docker-compose.yml` - Docker configuration
- `/.github/` - Development documentation

## 🔄 Standard Commands

```bash
# MANDATORY: Rebuild and restart Docker when testing changes
cd /Users/home/Huntarr/Huntarr.io && docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build

# Check logs for errors (ALWAYS do this after rebuild)
docker logs huntarr

# Search for code patterns
grep -r "pattern" src/
grep -r "pattern" frontend/

# Check running containers
docker ps

# Follow logs in real-time
docker logs -f huntarr
```

## ⚠️ Important Reminders

1. **NEVER use hard-coded absolute paths** - Must work on Windows, Mac, Docker, Linux
2. **ALWAYS use `os.path.join()`** for cross-platform path compatibility
3. **ALWAYS test cross-platform** - Docker vs bare metal behavior differs significantly
4. **ALWAYS test subpath scenarios** - Reverse proxy setups (e.g., `/huntarr/` prefix)
5. **Use relative URLs in frontend** - Avoid absolute `/api/` paths, use `./api/` instead
6. **Hunt for ALL hard-coded paths** - Use `grep -r "/config\|/app\|/data" src/` before any release
7. **Check for undefined variables** in JavaScript before deploying
8. **Use environment detection** instead of hard-coded paths
9. **Create memories** for significant fixes and features
10. **Update version.txt** when making changes
11. **Test API endpoints** after backend changes
12. **Verify UI responsiveness** across different screen sizes
13. **Check logs after every rebuild** - `docker logs huntarr`

---

*This document should be referenced before starting any development work and updated when new patterns are discovered.*
