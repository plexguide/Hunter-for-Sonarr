document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated
    const token = localStorage.getItem('huntarr_token');
    const username = localStorage.getItem('huntarr_username');
    
    if (!token) {
        // Redirect to login page if not authenticated
        window.location.href = '/login.html';
        return;
    }
    
    // Show username in header
    document.getElementById('username-display').textContent = username || 'User';
    
    // Tab navigation
    const tabLinks = document.querySelectorAll('nav ul li a[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get tab id
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all tabs
            tabLinks.forEach(tab => tab.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to current tab
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Handle logout
    document.getElementById('logoutBtn').addEventListener('click', function(e) {
        e.preventDefault();
        
        // Call logout API
        fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(() => {
            // Clear local storage and redirect to login
            localStorage.removeItem('huntarr_token');
            localStorage.removeItem('huntarr_username');
            window.location.href = '/login.html';
        })
        .catch(error => {
            console.error('Logout error:', error);
            
            // Force logout even if API fails
            localStorage.removeItem('huntarr_token');
            localStorage.removeItem('huntarr_username');
            window.location.href = '/login.html';
        });
    });
    
    // Load services status
    loadServicesStatus();
    
    // Refresh status button
    document.getElementById('refreshStatus').addEventListener('click', function() {
        loadServicesStatus();
    });
    
    // Settings tabs
    function openSettingsTab(evt, tabName) {
        const tabcontent = document.getElementsByClassName("tabcontent");
        for (let i = 0; i < tabcontent.length; i++) {
            tabcontent[i].classList.remove("active");
        }
        
        const tablinks = document.getElementsByClassName("tablinks");
        for (let i = 0; i < tablinks.length; i++) {
            tablinks[i].classList.remove("active");
        }
        
        document.getElementById(tabName).classList.add("active");
        evt.currentTarget.classList.add("active");
    }
    
    // Make openSettingsTab function available globally
    window.openSettingsTab = openSettingsTab;
    
    // Load settings for each service
    loadSettings('sonarr');
    loadSettings('radarr');
    loadSettings('lidarr');
    loadSettings('readarr');
    loadUserSettings();
    
    // Service form submission handlers
    document.getElementById('sonarrForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings('sonarr');
    });
    
    document.getElementById('radarrForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings('radarr');
    });
    
    document.getElementById('lidarrForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings('lidarr');
    });
    
    document.getElementById('readarrForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings('readarr');
    });
    
    // User settings form submission
    document.getElementById('userForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveUserSettings();
    });
    
    // Test connection buttons
    document.getElementById('testSonarr').addEventListener('click', function() {
        testConnection('sonarr');
    });
    
    document.getElementById('testRadarr').addEventListener('click', function() {
        testConnection('radarr');
    });
    
    document.getElementById('testLidarr').addEventListener('click', function() {
        testConnection('lidarr');
    });
    
    document.getElementById('testReadarr').addEventListener('click', function() {
        testConnection('readarr');
    });
    
    // 2FA toggle for user settings
    document.getElementById('enable2FAUser').addEventListener('change', function() {
        document.getElementById('twoFactorUserSection').style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            generateUserTwoFactorSetup();
        }
    });
    
    // Copy user secret key to clipboard
    document.getElementById('copyUserSecret').addEventListener('click', function() {
        const secretKey = document.getElementById('userSecretKey');
        secretKey.select();
        document.execCommand('copy');
        alert('Secret key copied to clipboard');
    });
    
    // Service action buttons (Run Missing/Upgrade)
    const actionButtons = document.querySelectorAll('[data-service][data-action]');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const service = this.getAttribute('data-service');
            const action = this.getAttribute('data-action');
            triggerServiceAction(service, action);
        });
    });
    
    // Load logs
    loadLogs();
    
    // Refresh logs button
    document.getElementById('refreshLogs').addEventListener('click', function() {
        loadLogs();
    });
    
    // Clear logs button
    document.getElementById('clearLogs').addEventListener('click', function() {
        clearLogs();
    });
    
    // Log service filter
    document.getElementById('logServiceFilter').addEventListener('change', function() {
        loadLogs();
    });
    
    // Functions
    
    function loadServicesStatus() {
        fetch('/api/status', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateServiceStatus('sonarr', data.services.sonarr);
                updateServiceStatus('radarr', data.services.radarr);
                updateServiceStatus('lidarr', data.services.lidarr);
                updateServiceStatus('readarr', data.services.readarr);
            }
        })
        .catch(error => {
            console.error('Error loading service status:', error);
        });
    }
    
    function updateServiceStatus(service, status) {
        const statusElement = document.getElementById(`${service}Status`);
        const missingElement = document.getElementById(`${service}Missing`);
        const upgradesElement = document.getElementById(`${service}Upgrades`);
        const lastRunElement = document.getElementById(`${service}LastRun`);
        
        if (status.active) {
            statusElement.textContent = 'Online';
            statusElement.classList.add('online');
            statusElement.classList.remove('offline');
            
            missingElement.textContent = status.missing || '0';
            upgradesElement.textContent = status.upgrades || '0';
            lastRunElement.textContent = status.lastRun || 'Never';
        } else {
            statusElement.textContent = 'Offline';
            statusElement.classList.add('offline');
            statusElement.classList.remove('online');
            
            missingElement.textContent = '--';
            upgradesElement.textContent = '--';
            lastRunElement.textContent = '--';
        }
    }
    
    function loadSettings(service) {
        fetch(`/api/settings/${service}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const settings = data.settings;
                
                // Populate form fields
                for (const key in settings) {
                    const element = document.getElementById(`${service}_${key}`);
                    if (element) {
                        if (element.type === 'checkbox') {
                            element.checked = settings[key];
                        } else {
                            element.value = settings[key];
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error(`Error loading ${service} settings:`, error);
        });
    }
    
    function saveSettings(service) {
        const form = document.getElementById(`${service}Form`);
        const formData = new FormData(form);
        
        const settings = {};
        
        // Convert form data to JSON object
        formData.forEach((value, key) => {
            // Extract actual key from input id
            const actualKey = key;
            
            // Set appropriate value type
            const element = document.getElementById(`${service}_${actualKey}`);
            if (element.type === 'checkbox') {
                settings[actualKey] = element.checked;
            } else if (element.type === 'number') {
                settings[actualKey] = parseInt(value);
            } else {
                settings[actualKey] = value;
            }
        });
        
        // Add checkbox fields that might not be included in formData when unchecked
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            const key = checkbox.name;
            if (!formData.has(key)) {
                settings[key] = false;
            }
        });
        
        fetch(`/api/settings/${service}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`${service.charAt(0).toUpperCase() + service.slice(1)} settings saved successfully!`);
            } else {
                alert(`Failed to save ${service} settings: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Error saving ${service} settings:`, error);
            alert(`Error saving ${service} settings`);
        });
    }
    
    function testConnection(service) {
        const apiKey = document.getElementById(`${service}_api_key`).value;
        const appUrl = document.getElementById(`${service}_app_url`).value;
        
        if (!apiKey || !appUrl) {
            alert('API Key and App URL are required for testing connection');
            return;
        }
        
        fetch(`/api/test-connection/${service}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                api_key: apiKey,
                app_url: appUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Connection to ${service} successful!`);
            } else {
                alert(`Connection to ${service} failed: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Error testing ${service} connection:`, error);
            alert(`Error testing ${service} connection`);
        });
    }
    
    function loadUserSettings() {
        fetch('/api/user/settings', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('username').value = data.username;
                document.getElementById('enable2FAUser').checked = data.has2FA;
            }
        })
        .catch(error => {
            console.error('Error loading user settings:', error);
        });
    }
    
    function saveUserSettings() {
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmNewPassword = document.getElementById('confirmNewPassword').value;
        const enable2FA = document.getElementById('enable2FAUser').checked;
        const verificationCode = document.getElementById('userVerificationCode').value;
        const secretKey = document.getElementById('userSecretKey').value;
        
        // Validate passwords
        if (newPassword && !currentPassword) {
            alert('Current password is required to set a new password');
            return;
        }
        
        if (newPassword && newPassword !== confirmNewPassword) {
            alert('New passwords do not match');
            return;
        }
        
        if (enable2FA && !verificationCode) {
            alert('Verification code is required for 2FA setup');
            return;
        }
        
        const settings = {
            currentPassword,
            newPassword: newPassword || null,
            enable2FA,
            secretKey: enable2FA ? secretKey : null,
            verificationCode: enable2FA ? verificationCode : null
        };
        
        fetch('/api/user/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('User settings saved successfully!');
                
                // Clear password fields
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmNewPassword').value = '';
                document.getElementById('userVerificationCode').value = '';
            } else {
                alert(`Failed to save user settings: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error saving user settings:', error);
            alert('Error saving user settings');
        });
    }
    
    function generateUserTwoFactorSetup() {
        fetch('/api/auth/generate-2fa-secret', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Display secret key
                document.getElementById('userSecretKey').value = data.secretKey;
                
                // Generate and display QR code
                const qrCodeContainer = document.getElementById('userQrCode');
                qrCodeContainer.innerHTML = '';
                
                new QRCode(qrCodeContainer, {
                    text: data.otpAuthUrl,
                    width: 200,
                    height: 200,
                    colorDark: "#000000",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.H
                });
            } else {
                alert(`Failed to generate 2FA secret: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('2FA setup error:', error);
            alert('An error occurred while setting up 2FA');
        });
    }
    
    function triggerServiceAction(service, action) {
        fetch(`/api/services/${service}/${action}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`${action.replace('-', ' ')} action for ${service} has been triggered`);
            } else {
                alert(`Failed to trigger ${action} for ${service}: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Error triggering ${action} for ${service}:`, error);
            alert(`Error triggering ${action} for ${service}`);
        });
    }
    
    function loadLogs() {
        const serviceFilter = document.getElementById('logServiceFilter').value;
        
        fetch(`/api/logs?service=${serviceFilter}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const logOutput = document.getElementById('logOutput');
                logOutput.innerHTML = '';
                
                if (data.logs.length === 0) {
                    logOutput.textContent = 'No logs available';
                } else {
                    data.logs.forEach(log => {
                        logOutput.innerHTML += `${log}\n`;
                    });
                    
                    // Scroll to bottom
                    logOutput.scrollTop = logOutput.scrollHeight;
                }
            }
        })
        .catch(error => {
            console.error('Error loading logs:', error);
        });
    }
    
    function clearLogs() {
        const serviceFilter = document.getElementById('logServiceFilter').value;
        
        if (confirm(`Are you sure you want to clear the ${serviceFilter === 'all' ? 'all' : serviceFilter} logs?`)) {
            fetch(`/api/logs/clear?service=${serviceFilter}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Logs cleared successfully');
                    loadLogs();
                } else {
                    alert(`Failed to clear logs: ${data.message}`);
                }
            })
            .catch(error => {
                console.error('Error clearing logs:', error);
                alert('Error clearing logs');
            });
        }
    }
});
