# Huntarr Development Memory

## Version 7.3.10 - Comprehensive UI Improvements

**Date:** 2025-05-25  
**Summary:** Major release addressing multiple UI/UX issues related to low usage mode, countdown timers, and user feedback accuracy.

**Key Improvements:**
1. **Low Usage Mode Stats Fix** - Fixed incorrect stats display when low usage mode is enabled
2. **Countdown Timer Startup** - Changed "Error Loading" to "Waiting for Cycle" during startup
3. **Reset Button Behavior** - Improved "Refreshing" feedback to stay until genuinely new data is available
4. **Development Guidelines** - Added version number management guidelines

**Files Modified:**
- `frontend/static/js/new-main.js` - Low usage mode detection and stats display fixes
- `frontend/static/js/cycle-countdown.js` - Startup messaging and reset behavior improvements  
- `.github/listen.MD` - Added version number management guidelines

**Tags:** ["major_release", "ui_improvements", "low_usage_mode", "countdown_timers", "user_experience"]

---

## Bug Fix: Low Usage Mode Stats Display Issue (v7.3.10)

**Date:** 2025-05-25  
**Issue:** When low usage mode is enabled, stats on the home page sometimes display incorrect numbers (showing old/cached values instead of current stats).  
**Root Cause:** Low usage mode's `disableIntensiveRendering()` function throttles `requestAnimationFrame` to only allow calls every 500ms, returning `null` for most calls. The `animateNumber()` function in `updateStatsDisplay()` relies on `requestAnimationFrame` for smooth number animations, but when throttled, the animations don't complete properly, leaving stats displaying incorrect values. Additionally, there was a race condition between stats loading and low usage mode detection.

**Solution:** 
1. **v7.4.0:** Modified `updateStatsDisplay()` function to detect when low usage mode is enabled and bypass animations entirely.
2. **v7.4.1:** Fixed race condition by ensuring low usage mode is checked before stats are loaded, and added robust multi-source detection for low usage mode state.

**Files Modified:**
- `frontend/static/js/new-main.js` - Added low usage mode detection, fixed initialization order, and improved state detection

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

## UI Improvement: Countdown Timer Startup Messaging (v7.3.10)

**Date:** 2025-05-25  
**Issue:** When Docker container starts/restarts, countdown timers show "Error Loading" initially, which is confusing to users since it's not actually an error - the timer is just waiting for the first app cycle to complete so it can calculate the next cycle time.  
**Root Cause:** The `displayLoadError()` function in `cycle-countdown.js` was showing "Error Loading" whenever the sleep.json file wasn't available, which happens normally during startup before the first cycle completes.

**Solution:** 
1. Renamed `displayLoadError()` to `displayWaitingForCycle()` for clarity
2. Changed the message from "Error Loading" to "Waiting for Cycle" 
3. Applied the same light blue color (#00c2ce) and refreshing-state class as used for normal refreshing
4. Updated comments and error handling to distinguish between startup waiting vs actual errors
5. Improved `updateTimerError()` to show proper error styling for actual connection issues

**Files Modified:**
- `frontend/static/js/cycle-countdown.js` - Improved startup messaging and error handling

**Code Changes:**
```javascript
// Before: Confusing error message during normal startup
timerValue.textContent = 'Error Loading';
timerValue.classList.add('error');

// After: Clear waiting message with proper styling
timerValue.textContent = 'Waiting for Cycle';
timerValue.classList.add('refreshing-state');
timerValue.style.color = '#00c2ce'; // Light blue like refreshing state
```

**User Experience:** Users now see "Waiting for Cycle" in light blue during startup instead of the alarming "Error Loading" message, making it clear that the system is working normally and just waiting for the first cycle to complete.

**Tags:** ["ui_improvement", "frontend", "countdown_timer", "startup", "user_experience"]

## UI Improvement: Countdown Timer Reset Behavior (v7.3.10)

**Date:** 2025-05-25  
**Issue:** When pressing the reset button on countdown timers, "Refreshing" message only stays for about 1 second then disappears, which is misleading because the actual reset process takes much longer (the app needs to complete a full cycle before new timer data is available).  
**Root Cause:** The reset button logic was using a simple 2-second timeout before fetching new data, but the actual reset process can take several minutes depending on the app's cycle duration.

**Solution:** 
1. Implemented intelligent polling system that keeps "Refreshing" displayed until actual new timer data is available
2. Added `data-waiting-for-reset` attribute to track timers waiting for reset data
3. Modified `updateTimerDisplay()` to respect the waiting state and not override "Refreshing" message
4. Added `startResetPolling()` function that polls every 5 seconds for up to 5 minutes
5. **CRITICAL FIX**: Store original cycle time before reset and only consider reset complete when receiving a *different* cycle time
6. Only removes "Refreshing" when genuinely new countdown data is received (not just the same old data)

**Files Modified:**
- `frontend/static/js/cycle-countdown.js` - Improved reset button behavior and polling logic
- `.github/listen.MD` - Added guidance to not update version numbers automatically

**Code Changes:**
```javascript
// Before: Simple timeout that was misleading
setTimeout(() => {
    fetchFromSleepJson();
}, 2000);

// After: Intelligent polling that waits for genuinely new data
function startResetPolling(app) {
    const pollInterval = setInterval(() => {
        fetchFromSleepJson().then(() => {
            if (nextCycleTimes[app]) {
                const currentCycleTime = nextCycleTimes[app].getTime();
                const originalCycleTime = parseInt(timerElement.getAttribute('data-original-cycle-time'));
                
                // Only consider reset complete if we have a DIFFERENT cycle time
                if (originalCycleTime === null || currentCycleTime !== originalCycleTime) {
                    // Genuinely new data received, stop polling and update display
                    timerElement.removeAttribute('data-waiting-for-reset');
                    clearInterval(pollInterval);
                    updateTimerDisplay(app);
                } else {
                    // Same old data, keep polling
                    console.log('Same cycle time, continuing to poll for new data');
                }
            }
        });
    }, 5000); // Poll every 5 seconds
}
```

**User Experience:** Users now see "Refreshing" for the appropriate duration until the reset process actually completes and new countdown data is available, providing accurate feedback about the system state.

**Tags:** ["ui_improvement", "frontend", "countdown_timer", "reset_behavior", "polling", "user_feedback"]

--- 