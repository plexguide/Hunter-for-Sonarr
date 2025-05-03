// Direct reset button implementation - completely separate from the regular UI
// This will add a new red button directly to the stateful management section

// Run this code as soon as this script is loaded
(function() {
    function insertDirectResetButton() {
        // Look for the stateful header row
        const headerRow = document.querySelector('.stateful-header-row');
        
        if (!headerRow) {
            // If we can't find it, try again soon
            console.log('Stateful header not found, will try again in 1 second');
            setTimeout(insertDirectResetButton, 1000);
            return;
        }
        
        // Check if our button already exists to avoid duplicates
        if (document.getElementById('emergency_reset_btn')) {
            return;
        }
        
        console.log('Found stateful header, adding emergency reset button');
        
        // Create the new button
        const resetButton = document.createElement('button');
        resetButton.id = 'emergency_reset_btn';
        resetButton.innerText = '🔥 EMERGENCY RESET 🔥';
        resetButton.style.background = 'linear-gradient(to right, #ff0000, #8b0000)';
        resetButton.style.color = 'white';
        resetButton.style.fontWeight = 'bold';
        resetButton.style.border = 'none';
        resetButton.style.borderRadius = '4px';
        resetButton.style.padding = '8px 16px';
        resetButton.style.marginLeft = '15px';
        resetButton.style.cursor = 'pointer';
        resetButton.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
        
        // Add click handler for the new button
        resetButton.onclick = function() {
            if (confirm('⚠️ EMERGENCY RESET: Are you absolutely sure you want to reset all processed media IDs? This cannot be undone!')) {
                
                // Show loading state
                this.disabled = true;
                this.innerText = '⏳ Resetting...';
                this.style.background = '#666';
                
                // Make direct API call
                fetch('/api/stateful/reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Server returned status ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    alert('✅ Success! Stateful management has been reset.');
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Reset failed:', error);
                    alert('❌ Reset failed: ' + error.message);
                    
                    // Restore button state
                    this.disabled = false;
                    this.innerText = '🔥 EMERGENCY RESET 🔥';
                    this.style.background = 'linear-gradient(to right, #ff0000, #8b0000)';
                });
            }
            
            // Prevent event propagation
            return false;
        };
        
        // Add the button to the page
        headerRow.appendChild(resetButton);
        console.log('Emergency reset button added successfully');
    }
    
    // Try to add the button immediately
    insertDirectResetButton();
    
    // Also try when the DOM is loaded
    document.addEventListener('DOMContentLoaded', insertDirectResetButton);
    
    // And again when everything is fully loaded
    window.addEventListener('load', insertDirectResetButton);
})();
