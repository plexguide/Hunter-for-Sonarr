# Huntarr Development Memory

## Bug Fix: Low Usage Mode Stats Display Issue (v7.4.0 - v7.4.1)

**Date:** 2025-05-25  
**Issue:** When low usage mode is enabled, stats on the home page sometimes display incorrect numbers (showing old/cached values instead of current stats).  
**Root Cause:** Low usage mode's `disableIntensiveRendering()` function throttles `requestAnimationFrame` to only allow calls every 500ms, returning `null` for most calls. The `animateNumber()` function in `updateStatsDisplay()` relies on `requestAnimationFrame` for smooth number animations, but when throttled, the animations don't complete properly, leaving stats displaying incorrect values. Additionally, there was a race condition between stats loading and low usage mode detection.

**Solution:** 
1. **v7.4.0:** Modified `updateStatsDisplay()` function to detect when low usage mode is enabled and bypass animations entirely.
2. **v7.4.1:** Fixed race condition by ensuring low usage mode is checked before stats are loaded, and added robust multi-source detection for low usage mode state.

**Files Modified:**
- `frontend/static/js/new-main.js` - Added low usage mode detection, fixed initialization order, and improved state detection
- `version.txt` - Incremented to 7.4.1

**Code Changes:**
```javascript
// v7.4.0: Basic low usage mode detection
const isLowUsageMode = document.body.classList.contains('low-usage-mode');

// v7.4.1: Robust multi-source detection
isLowUsageModeEnabled: function() {
    const hasLowUsageClass = document.body.classList.contains('low-usage-mode');
    const standaloneModuleEnabled = window.LowUsageMode && window.LowUsageMode.isEnabled && window.LowUsageMode.isEnabled();
    const indicator = document.getElementById('low-usage-mode-indicator');
    const indicatorVisible = indicator && indicator.style.display !== 'none' && indicator.style.display !== '';
    return hasLowUsageClass || standaloneModuleEnabled || indicatorVisible;
}

// Fixed initialization order to check low usage mode before loading stats
this.checkLowUsageMode().then(() => {
    if (window.location.pathname === '/') {
        this.loadMediaStats();
    }
})
```

**Testing:** Verified that stats display correctly both with low usage mode enabled (direct values) and disabled (animated values), and that the race condition is resolved.

**Tags:** ["bug_fix", "frontend", "low_usage_mode", "stats", "animations", "race_condition"]

--- 