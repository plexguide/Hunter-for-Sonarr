# Huntarr Development Instructions

This document serves as a constant reminder and reference for common development tasks, debugging procedures, and fix patterns in the Huntarr codebase.

## 🚀 Version Update Workflow

**When making changes:**

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

### 1. Frontend Log Regex Issues (Logs Not Showing for Specific Apps)

**Symptoms:**
- Logs are being generated and written to log files correctly
- Backend log streaming endpoint serves logs properly (e.g., `/logs?app=huntarr.hunting`, `/logs?app=sonarr`, etc.)
- Frontend shows "Connected" status but no logs appear when specific app is selected
- Other app logs work fine, but one or more specific apps show no logs
- Issue affects any app type (huntarr.hunting, sonarr, radarr, new custom apps, etc.)

**Root Cause:**
- Malformed regex pattern in frontend JavaScript with double backslashes
- Regex fails to parse log messages, preventing proper app type categorization
- Logs exist but aren't displayed due to failed pattern matching
- Affects any app whose logs don't match the broken regex pattern

**Debugging Steps:**
1. **Check if logs exist in container for the affected app:**
   ```bash
   # Replace 'hunting' with the actual app log file name
   docker exec huntarr cat /config/logs/hunting.log
   docker exec huntarr cat /config/logs/sonarr.log
   docker exec huntarr cat /config/logs/[app_name].log
   ```

2. **Test backend log streaming for the affected app:**
   ```bash
   # Test with the specific app parameter that's not working
   curl -N -s "http://localhost:9705/logs?app=huntarr.hunting" | head -10
   curl -N -s "http://localhost:9705/logs?app=sonarr" | head -10
   curl -N -s "http://localhost:9705/logs?app=[app_name]" | head -10
   ```

3. **Check browser console** for JavaScript regex errors

4. **Test log format compatibility:**
   ```bash
   # Check the actual log format to ensure it matches expected pattern
   docker exec huntarr tail -5 /config/logs/[app_name].log
   ```

**Fix Pattern:**
```javascript
// ❌ BROKEN - Double backslashes break regex matching for ALL apps
const logRegex = /^(?:\\[(\\w+)\\]\\s)?([\\d\\-]+\\s[\\d:]+)\\s-\\s([\\w\\.]+)\\s-\\s(\\w+)\\s-\\s(.*)$/;

// ✅ FIXED - Proper regex escaping works for ALL app log formats
const logRegex = /^(?:\[(\w+)\]\s)?([^\s]+\s[^\s]+)\s-\s([\w\.]+)\s-\s(\w+)\s-\s(.*)$/;
```

**Files to Check:**
- `/frontend/static/js/new-main.js` - `connectEventSource()` method
- Look for `logRegex` variable and `logString.match(logRegex)` usage
- Check app type categorization logic in the same function

**App Type Categorization Check:**
Ensure the affected app is included in the categorization logic:
```javascript
// Verify the app is in the known apps list
if (['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'swaparr', 'hunting', 'your_new_app'].includes(possibleApp)) {
    logAppType = possibleApp;
}

// And in the pattern matching for system logs
const patterns = {
    'sonarr': ['episode', 'series', 'tv show', 'sonarr'],
    'radarr': ['movie', 'film', 'radarr'],
    'lidarr': ['album', 'artist', 'track', 'music', 'lidarr'],
    'readarr': ['book', 'author', 'readarr'],
    'whisparr': ['scene', 'adult', 'whisparr'],
    'eros': ['eros', 'whisparr v3', 'whisparrv3'],
    'swaparr': ['added strike', 'max strikes reached', 'swaparr'],
    'hunting': ['hunt manager', 'discovery tracker', 'hunting', 'hunt'],
    'your_new_app': ['keyword1', 'keyword2', 'your_new_app']  // Add patterns for new apps
};
```

**Verification:**
1. Rebuild container: `docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build`
2. Check frontend logs display correctly for ALL app types
3. Verify log categorization works (logs appear when each specific app is selected)
4. Test with multiple apps to ensure the fix is universal

**LESSON LEARNED:** Always test regex patterns with actual log data from ALL app types. Double backslashes in JavaScript regex literals cause pattern matching failures that silently prevent log categorization without obvious error messages. This issue can affect any app (existing or newly added) whose logs don't match the malformed regex pattern. When adding new apps, always verify their logs display correctly in the frontend.

### 2. Timer Loading Errors ("Error Loading" on Dashboard)

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

### 3. JavaScript "Variable Not Defined" Errors in Settings

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

### 4. Settings Save Issues

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

### 5. UI Element Visibility Issues

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

## 🚨 CRITICAL: Subpath Compatibility Lessons (PR #527)

**PROBLEM:** Huntarr broke when deployed in subdirectories (e.g., `domain.com/huntarr/`) due to absolute URL references that failed in subpath environments.

**SYMPTOMS:**
- Application works at root domain (`domain.com`) but fails in subdirectories
- Navigation redirects break (redirect to wrong URLs)
- CSS/JS resources fail to load
- API calls return 404 errors
- Setup process gets stuck

### 🔧 Critical Fix Patterns from PR #527

#### 1. JavaScript Navigation URLs - HIGH PRIORITY
**❌ BROKEN:**
```javascript
// Absolute URLs break in subpaths
window.location.href = '/';  // Redirects to domain.com instead of domain.com/huntarr/
```

**✅ FIXED:**
```javascript
// Relative URLs work in all environments
window.location.href = './';  // Correctly redirects to current subpath
```

**Files to Check:**
- `/frontend/static/js/new-main.js` - Settings save redirects
- `/frontend/templates/setup.html` - Setup completion redirects
- Any JavaScript with `window.location.href = '/'`

#### 2. CSS Resource Loading - HIGH PRIORITY
**❌ BROKEN:**
```html
<!-- Multiple CSS files with incorrect names -->
<link rel="stylesheet" href="./static/css/variables.css">
<link rel="stylesheet" href="./static/css/styles.css">
```

**✅ FIXED:**
```html
<!-- Single consolidated CSS file -->
<link rel="stylesheet" href="./static/css/style.css">
```

**Files to Check:**
- `/frontend/templates/base.html` - Main CSS references
- `/frontend/templates/components/head.html` - Head CSS includes
- Any template with CSS `<link>` tags

#### 3. API Endpoint URLs
**✅ GOOD PATTERN (Already implemented):**
```javascript
// Relative API calls work in subpaths
fetch('./api/sleep.json')  // ✅ Works
fetch('/api/sleep.json')   // ❌ Breaks in subpaths
```

### 🔍 Subpath Testing Checklist

**MANDATORY before any frontend changes:**
- [ ] Test navigation from every page (all redirects work)
- [ ] Test CSS/JS resources load correctly
- [ ] Test API calls work from all pages
- [ ] Test setup process completion
- [ ] Test authentication flow redirects
- [ ] Test with reverse proxy configuration: `domain.com/huntarr/`

### 🚨 Subpath Anti-Patterns to AVOID

1. **❌ NEVER use absolute URLs in JavaScript:**
   ```javascript
   window.location.href = '/';           // BREAKS subpaths
   window.location.href = '/settings';   // BREAKS subpaths
   fetch('/api/endpoint');               // BREAKS subpaths
   ```

2. **❌ NEVER hardcode root paths in templates:**
   ```html
   <link href="/static/css/style.css">   <!-- BREAKS subpaths -->
   <script src="/static/js/app.js">      <!-- BREAKS subpaths -->
   ```

3. **❌ NEVER assume root deployment:**
   ```python
   redirect('/')  # BREAKS in Flask routes with subpaths
   ```

### 🎯 Subpath Prevention Strategy

**Before committing any frontend changes:**

1. **Search for absolute URL patterns:**
   ```bash
   grep -r "href=\"/" frontend/
   grep -r "src=\"/" frontend/
   grep -r "window.location.href = '/" frontend/
   grep -r "fetch('/" frontend/
   ```

2. **Test deployment scenarios:**
   - Root deployment: `http://localhost:9705/`
   - Subpath deployment: `http://localhost:9705/huntarr/`
   - Reverse proxy: `https://domain.com/huntarr/`

3. **Verify all navigation works:**
   - Home → Settings → Home
   - Setup flow completion
   - Authentication redirects
   - Error page redirects

**LESSON LEARNED:** Subpath compatibility issues are SILENT FAILURES that only surface in production reverse proxy environments. Always test with subpath configurations before deploying.

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
7. **Fix the actual file, don't create new ones** - When fixing bugs, modify the source file directly instead of creating correction/wrapper files
8. **ALWAYS test in Docker, never execute local code** - Use Docker containers for all testing and development
9. **Don't create local configs** - Check configurations inside the Docker container instead
10. **Never modify files inside Docker container** - Update codebase then rebuild Docker to test changes
11. **Always rebuild container to test changes** - `docker-compose down && docker-compose up --build`
12. **Don't add to new-main.js** - Create new JS files and organize in subfolders for better structure
13. **Don't add to main.css** - Create page-specific CSS files instead of modifying the main stylesheet
14. **Check for undefined variables** in JavaScript before deploying
15. **Use environment detection** instead of hard-coded paths
16. **Create memories** for significant fixes and features
17. **DO NOT update version.txt automatically** - Version numbers are manually managed by the user during publishing
18. **Test API endpoints** after backend changes
19. **Verify UI responsiveness** across different screen sizes
20. **Check logs after every rebuild** - `docker logs huntarr`
21. **For docs branches (docs-*):** Automatically commit and publish changes when working on documentation updates

## 📚 Documentation Branch Workflow

**When working on branches that start with `docs-`:**

1. **Auto-commit and publish** - Changes to documentation should be committed and published automatically
2. **Branch naming convention** - Use `docs-[issue-number]` or `docs-[feature-name]` format
3. **Scope** - Documentation branches are for `/docs` directory changes only
4. **Publishing** - Push changes to GitHub Pages automatically after commit

**Example workflow:**
```bash
# Working on docs-106 branch (current)
git add docs/
git commit -m "Add comprehensive FAQ with categorized sections and return-to-top functionality"
git push origin docs-106
```

---

*This document should be referenced before starting any development work and updated when new patterns are discovered.*

## Docker Development Workflow

When making changes to the codebase, follow this workflow:

1. **Make your changes** to the source code
2. **Rebuild the container** with baking enabled:
   ```bash
   docker-compose down && COMPOSE_BAKE=true docker-compose up -d --build
   ```
3. **Test your changes** by checking logs and functionality
4. **Check logs** if needed:
   ```bash
   docker logs huntarr -f
   ```

## Debugging Patterns

### Log Streaming Issues
If logs aren't showing in the frontend dropdown:
1. Check the log file mapping in `KNOWN_LOG_FILES` (web_server.py)
2. Verify the frontend regex patterns in `new-main.js` 
3. **Important**: Avoid double backslashes in regex patterns - they break pattern matching
4. Test with: `curl http://localhost:9705/api/logs/stream/huntarr.hunting`

### Dashboard Flash Issue (FOUC)
If the home page shows a flash of all apps before organizing correctly:
1. **Root cause**: Dashboard grid starts with `opacity: 0` to prevent flash, but JavaScript doesn't make it visible
2. **Solution**: Call `showDashboard()` in `huntarrUI.init()` to set `opacity: 1` after initialization
3. **Location**: `frontend/static/js/new-main.js` - add `this.showDashboard()` after setup is complete
4. **Key principle**: Always make hidden elements visible after JavaScript initialization is complete

### Cycle State Management
The smart `cyclelock` system provides reliable cycle state tracking:
1. **cyclelock: true** = App is running a cycle (shows "Running Cycle")
2. **cyclelock: false** = App is waiting (shows countdown timer)  
3. **Default on startup**: `cyclelock: true` (assumes cycles start immediately)
4. **Reset behavior**: Sets `cyclelock: true` to trigger immediate cycle start
5. **Automatic updates**: `start_cycle()` and `end_cycle()` functions manage state transitions
6. **Data preservation**: `_save_cycle_data()` preserves cyclelock when updating sleep.json

## Lessons Learned

1. **Regex patterns**: Double backslashes in JavaScript regex break pattern matching
2. **Timezone handling**: Always use UTC for consistent datetime calculations across containers
3. **State management**: Explicit state fields (like cyclelock) are more reliable than inferring state from timestamps
4. **FOUC prevention**: Hidden elements need explicit JavaScript to make them visible after initialization
5. **Log level optimization**: Move ALL verbose authentication, log streaming, and stats increment messages to DEBUG level to reduce log noise and improve readability. This includes:
   - Authentication messages: "Local Bypass Mode is DISABLED", "Request IP address", "Direct IP is a local network IP"
   - Log streaming messages: "Starting log stream", "Client disconnected", "Log stream generator finished"  
   - Stats messages: "STATS ONLY INCREMENT", "STATS INCREMENT", "Successfully incremented and verified", "Successfully wrote stats to file"
   - "Attempt to get user info failed: Not authenticated" messages in `routes/common.py`
6. **Logger name formatting consistency**: Use lowercase for logger name prefixes in log streaming. Change `name.upper()` to `name.lower()` in `web_server.py` log stream generator to ensure consistent formatting (e.g., "huntarr.hunting" instead of "HUNTARR.HUNTING").
7. **Sidebar content sizing**: When resizing sidebar elements, reduce all related dimensions proportionally (fonts, padding, margins, icon containers) while preserving key elements like logo icons. For 20% reduction: reduce font-size from 14px to 11px, padding from 12px to 10px, icon wrapper from 38px to 30px, etc. Always maintain visual hierarchy and usability while achieving the desired size reduction.
8. **Low Usage Mode Indicator Removal**:
   - Completely removed the visual indicator that appeared when Low Usage Mode was enabled
   - Modified `showIndicator()` function in `low-usage-mode.js` to not create any DOM elements
   - Updated `applyLowUsageMode()` function in `new-main.js` to remove indicator creation logic
   - Removed CSS styles for `#low-usage-mode-indicator` from `low-usage-mode.css`
   - Low Usage Mode now runs silently without any visual indicator for a cleaner interface
   - All performance optimizations (animation disabling, timer throttling) still work as intended
