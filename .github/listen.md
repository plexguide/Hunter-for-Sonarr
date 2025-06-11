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

### 6. CSS Loading Order/Specificity Issues
**Symptoms:** Inline component CSS styles not applying, especially mobile responsive changes
**Root Cause:** External CSS files (`responsive-fix.css`, `new-style.css`) load after component templates and override inline styles
**Fix:** Add critical responsive CSS to external files with higher specificity
```css
/* ❌ BROKEN - Inline component CSS gets overridden */
<!-- In component template -->
<style>
.app-stats-card.swaparr .stats-numbers {
    grid-template-columns: 1fr !important;
}
</style>

/* ✅ FIXED - Add to external CSS file */
/* File: frontend/static/css/responsive-fix.css */
@media (max-width: 768px) {
    .app-stats-card.swaparr .stats-numbers {
        display: grid !important;
        grid-template-columns: 1fr !important;
        /* Debug border for testing */
        border: 2px solid lime !important;
    }
}
```
**Debugging Technique:** Use colored debug borders to confirm CSS is loading
**Files:** `/frontend/static/css/responsive-fix.css`, `/frontend/static/css/new-style.css`

### 7. Info Icon Documentation Link Issues
**Symptoms:** Info icons (i) linking to wrong domains, localhost, or broken forum links
**Root Cause:** Hard-coded old links instead of GitHub documentation links
**Fix:** Use proper GitHub documentation pattern with specific anchors
```javascript
// ❌ BROKEN - Old forum or localhost links
<label><a href="https://huntarr.io/threads/name-field.18/" class="info-icon">
<label><a href="/Huntarr.io/docs/#/configuration" class="info-icon">
<label><a href="#" class="info-icon">

// ✅ FIXED - GitHub documentation with anchors
<label><a href="https://plexguide.github.io/Huntarr.io/apps/radarr.html#instances" class="info-icon">
<label><a href="https://plexguide.github.io/Huntarr.io/apps/radarr.html#skip-future-movies" class="info-icon">
<label><a href="https://plexguide.github.io/Huntarr.io/apps/swaparr.html#enable-swaparr" class="info-icon">
```
**Pattern:** `https://plexguide.github.io/Huntarr.io/apps/[app-name].html#[anchor]`
**Requirements:**
- Always use `https://plexguide.github.io/Huntarr.io/` domain
- Include `target="_blank" rel="noopener"` attributes
- Use specific anchors that match documentation headers
- Ensure documentation anchors exist before linking
**File:** `/frontend/static/js/settings_forms.js`

### 8. GitHub API Rate Limiting & Timeout Issues
**Symptoms:** Sponsor sections showing timeouts, empty data, or rate limit errors
**Root Cause:** Direct GitHub API calls from each installation hitting rate limits
**Fix:** Use GitHub Actions + static manifest approach (Matthieu's solution)
```python
# ❌ BROKEN - Direct API calls from each installation
response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)

# ✅ FIXED - Fetch from static manifest updated by GitHub Actions
response = requests.get("https://plexguide.github.io/Huntarr.io/manifest.json", timeout=10)
manifest_data = response.json()
sponsors = manifest_data.get('sponsors', [])
```
**Solution Pattern:**
1. **GitHub Action** runs on releases + daily schedule
2. **Fetches sponsors** using authenticated GraphQL API  
3. **Publishes manifest.json** to GitHub Pages with sponsors + version data
4. **Installations fetch** from static manifest (no authentication needed)
5. **No rate limits** since only the GitHub Action hits the API

**Benefits:**
- Each installation doesn't need GitHub API access
- No rate limiting issues for users
- Faster response times (static file vs API call)
- Automatic updates via GitHub Actions
- Fallback to cached data if manifest unavailable

**Files:** 
- `.github/workflows/update-manifest.yml` - GitHub Action workflow
- `src/primary/web_server.py` - Backend API endpoint
- GitHub Pages serves `manifest.json` automatically

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

### Proactive Violation Scanning
**Run these before every release to catch violations early:**
```bash
# 1. Absolute URL violations (most critical for subpath deployment)
echo "=== SCANNING FOR ABSOLUTE URL VIOLATIONS ==="
grep -r "fetch('/api/" frontend/ --include="*.js" | wc -l | xargs echo "fetch() absolute URLs:"
grep -r "window.location.href.*= '/" frontend/ --include="*.js" --include="*.html" | wc -l | xargs echo "redirect absolute URLs:"

# 2. Documentation link violations  
echo "=== SCANNING FOR DOCUMENTATION LINK VIOLATIONS ==="
grep -r "href.*plexguide.github.io" frontend/ --include="*.js" | grep -v "plexguide.github.io/Huntarr.io" | wc -l | xargs echo "wrong domain links:"

# 3. Hard-coded path violations
echo "=== SCANNING FOR HARD-CODED PATH VIOLATIONS ==="
grep -r "/config" src/ --include="*.py" | grep -v "_detect_environment\|_get.*path" | wc -l | xargs echo "hard-coded /config paths:"
grep -r "/app" src/ --include="*.py" | grep -v "_detect_environment\|_get.*path" | wc -l | xargs echo "hard-coded /app paths:"

# 4. Frontend-docs alignment check
echo "=== CHECKING FRONTEND-DOCS ALIGNMENT ==="
echo "Frontend anchor references:"
grep -r "href.*plexguide\.github\.io.*#" frontend/static/js/ | grep -o "#[^\"]*" | sort | uniq | wc -l
echo "Documentation anchors available:"
grep -r 'id="[^"]*"' docs/apps/ | grep -o 'id="[^"]*"' | sort | uniq | wc -l
```

### Path Hunting Commands
```bash
# Search for hard-coded paths (legacy)
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

### Systematic Issue Discovery
**When things don't work, don't guess - scan systematically:**
```bash
# 1. Check for violation patterns first
./violation_scan.sh  # From proactive practices above

# 2. Specific issue hunting
grep -r "EXACT_ERROR_TEXT" frontend/ src/ --include="*.js" --include="*.py"
grep -r "functionName\|variableName" frontend/ --include="*.js"
```

### Subpath Deployment Issues
**Symptoms:** Works on localhost, fails on domain.com/huntarr/
**Root Cause:** Absolute URLs that don't work in subdirectories
**Debug Process:**
1. Check browser network tab for 404s on absolute URLs
2. Search for absolute patterns: `grep -r "fetch('/api" frontend/`
3. Check redirects: `grep -r "window.location.href.*= '/" frontend/`
4. Verify all URLs are relative: `./api/` not `/api/`

### Frontend-Documentation Link Issues  
**Symptoms:** Info icons (i) lead to 404 or wrong pages
**Root Cause:** Mismatched frontend links vs documentation anchors
**Debug Process:**
1. Extract frontend anchor references: `grep -r "href.*#" frontend/static/js/ | grep -o "#[^\"]*"`
2. Extract doc anchors: `grep -r 'id="[^"]*"' docs/ | grep -o 'id="[^"]*"'`
3. Compare lists to find mismatches
4. Add missing anchors or fix links

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
5. **NEW:** Scan for hard-coded paths: `grep -r "/config\|/app" src/ | grep -v "_detect_environment"`

### JavaScript Issues
1. Check browser console for errors
2. Search for undefined variables: `grep -r "variableName" frontend/`
3. Verify HTML structure matches selectors
4. Compare with working functions
5. **NEW:** Check for absolute URL patterns causing 404s in subpaths

### CSS Issues
1. Check browser console for errors
2. Add debug borders: `border: 2px solid lime !important;`
3. Verify CSS loading order (external files vs inline)
4. Test specificity with `!important` declarations
5. Search for conflicting rules: `grep -r "className" frontend/static/css/`

### Settings Issues
1. Check form generation functions
2. Verify `getFormSettings()` method
3. Test save/load cycle
4. Check API endpoints
5. **NEW:** Verify info icon links point to existing documentation anchors

### Documentation Issues
**Symptoms:** Broken links, 404s, outdated information
**Debug Process:**
1. Test all links manually or with link checker
2. Verify features mentioned actually exist in codebase
3. Check frontend alignment with documentation
4. Audit FAQ against real support requests

## 📊 RECENT IMPROVEMENTS

### Systematic Code Violation Fixes (2024-12)
**Issue:** 71 systematic code violations discovered through comprehensive codebase analysis
**Root Cause:** Lack of proactive violation scanning and systematic fixing approach
**Solution:** Implemented systematic approach to finding and fixing violations

**Fixed Violations:**
1. **51 absolute fetch URLs** - All `/api/` calls converted to `./api/` for subpath compatibility
2. **15 outdated documentation links** - Fixed old domain references in settings_forms.js
3. **5 window.location.href absolute URLs** - Converted `/` redirects to `./` 
4. **Missing documentation anchors** - Added proper IDs to all referenced doc sections

**Key Files Modified:**
- `/frontend/static/js/settings_forms.js` - Documentation links and form generation
- `/frontend/static/js/new-main.js` - URL handling and redirects
- `/frontend/static/js/apps.js` - API calls and fetch operations
- All documentation files - Added missing anchor IDs

**Prevention Strategy:** Use systematic grep searches to catch violations early:
```bash
# Catch absolute URLs before they become problems
grep -r "fetch('/api/" frontend/ --include="*.js"
grep -r "window.location.href.*= '/" frontend/ --include="*.js" --include="*.html"
grep -r "href.*plexguide.github.io" frontend/ --include="*.js" | grep -v "plexguide.github.io/Huntarr.io"
```

### Documentation Reality Check & User Experience (2024-12)
**Issue:** Documentation promised features that didn't exist (standalone logs/history pages)
**Root Cause:** Feature documentation grew organically without reality checks
**Solution:** Systematic audit of promised vs actual features

**Changes:**
- Removed broken links to non-existent logs.html and history.html
- Updated features page to reflect actual functionality (Swaparr, Search Automation)
- Completely rewrote FAQ with real-world Docker problems and practical solutions
- Added prominent community help section on homepage with proper user flow

**Lessons Learned:**
- **Document what exists, not what's planned** - Only link to documentation that actually exists
- **FAQ should solve real problems** - Base content on actual support requests, not theoretical issues
- **User journey matters** - Help → Explanation → Setup → Community is better than promotional content

### Frontend-Documentation Alignment System (2024-12)
**Issue:** Frontend info icons linked to anchors that didn't exist in documentation
**Root Cause:** No systematic checking of frontend links against actual documentation
**Solution:** Implemented verification system for frontend→docs alignment

**Process:**
1. Extract all documentation links from frontend: `grep -r "plexguide.github.io.*#" frontend/`
2. Extract all anchor IDs from docs: `grep -r 'id="[^"]*"' docs/`
3. Cross-reference and fix mismatches
4. Add missing anchor IDs where content exists but ID missing

**Prevention:** Before any documentation changes, verify link alignment:
```bash
# Extract frontend links
grep -r "href.*plexguide\.github\.io.*#" frontend/static/js/ | grep -o "#[^\"]*" | sort | uniq

# Extract doc anchors  
grep -r 'id="[^"]*"' docs/apps/ | grep -o 'id="[^"]*"' | sort | uniq

# Compare results to catch mismatches
```

### Radarr Release Date Consistency (2024-12)
**Issue:** Missing movie searches respected `skip_future_releases` setting, but upgrade searches ignored it
**Solution:** Made upgrade behavior consistent with missing movie logic
**Changes:**
- Updated `src/primary/apps/radarr/upgrade.py` to check release dates
- Both missing and upgrade searches now respect `skip_future_releases` and `process_no_release_dates`
- Documentation updated to clarify behavior affects both search types
- Frontend info icons fixed to use GitHub documentation links

**User Benefit:** Consistent behavior - no more unexpected future movie upgrades

## ⚠️ ANTI-PATTERNS TO AVOID

1. **❌ Hard-coded absolute paths:** `/config/file.json`
2. **❌ Absolute URLs in frontend:** `/api/endpoint`, `window.location.href = '/'`
3. **❌ Modifying files inside containers**
4. **❌ Creating temporary/helper files instead of fixing source**
5. **❌ Auto-committing without approval**
6. **❌ Double backslashes in regex patterns**
7. **❌ Testing only in Docker (must test bare metal)**
8. **❌ Adding responsive CSS to component templates (use external CSS files)**
9. **❌ Not using debug borders to test CSS loading**
10. **❌ Inconsistent behavior between missing/upgrade logic** - Always check both implement same filtering
11. **❌ Reactive violation fixing** - Don't wait for problems to appear, scan proactively
12. **❌ Documentation that promises non-existent features** - Only document what actually exists
13. **❌ Frontend links without verifying documentation anchors exist** - Always cross-check
14. **❌ Organic feature growth without reality checks** - Audit promised vs actual features regularly
15. **❌ Theoretical FAQ content** - Base FAQ on real user problems and support requests

## 🚨 PROACTIVE DEVELOPMENT PRACTICES

### Pre-Commit Violation Scanning
**ALWAYS run before any commit to catch violations early:**
```bash
# Create violation_scan.sh for easy reuse
echo "=== HUNTARR VIOLATION SCAN ==="
echo "1. Absolute URL violations (breaks subpath deployment):"
echo "   fetch() absolute URLs: $(grep -r "fetch('/api/" frontend/ --include="*.js" | wc -l)"
echo "   redirect absolute URLs: $(grep -r "window.location.href.*= '/" frontend/ --include="*.js" --include="*.html" | wc -l)"
echo ""
echo "2. Documentation violations:"
echo "   Wrong domain links: $(grep -r "href.*plexguide.github.io" frontend/ --include="*.js" | grep -v "plexguide.github.io/Huntarr.io" | wc -l)"
echo ""
echo "3. Hard-coded path violations:"
echo "   /config paths: $(grep -r "/config" src/ --include="*.py" | grep -v "_detect_environment\|_get.*path" | wc -l)"
echo "   /app paths: $(grep -r "/app" src/ --include="*.py" | grep -v "_detect_environment\|_get.*path" | wc -l)"
echo ""
echo "4. Frontend-docs alignment:"
echo "   Frontend anchors: $(grep -r "href.*plexguide\.github\.io.*#" frontend/static/js/ 2>/dev/null | grep -o "#[^\"]*" | sort | uniq | wc -l)"
echo "   Doc anchors: $(grep -r 'id="[^"]*"' docs/apps/ 2>/dev/null | grep -o 'id="[^"]*"' | sort | uniq | wc -l)"
echo "=== SCAN COMPLETE ==="
```

### Documentation Reality Audit Process
**Before any documentation changes:**
1. **Verify features exist**: Don't document planned features, only existing ones
2. **Check all links work**: Test every link in documentation
3. **Verify frontend alignment**: Ensure info icons point to existing anchors
4. **FAQ reality check**: Base content on actual support requests, not theoretical issues

**Commands to audit documentation:**
```bash
# 1. Find all links in documentation
grep -r "href=" docs/ | grep -v "^#" | cut -d'"' -f2 | sort | uniq

# 2. Find all frontend documentation links
grep -r "plexguide.github.io" frontend/static/js/ | grep -o "https://[^\"]*"

# 3. Check anchor mismatches
diff <(grep -r "href.*#" frontend/static/js/ | grep -o "#[^\"]*" | sort | uniq) \
     <(grep -r 'id="[^"]*"' docs/ | grep -o 'id="[^"]*"' | sed 's/id="//' | sed 's/"$//' | sort | uniq)
```

### User Experience Validation
**Before major UI changes:**
1. **Test user journey**: Help → Explanation → Setup → Community
2. **Verify community links work**: Discord, GitHub Issues, Reddit
3. **Check mobile responsiveness**: Test all breakpoints
4. **Validate against real user problems**: Base features on actual use cases

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
