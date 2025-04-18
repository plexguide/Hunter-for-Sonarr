document.addEventListener('DOMContentLoaded', function() {
    const setupForm = document.getElementById('setupForm');
    const setupError = document.getElementById('setupError');
    const setupSuccess = document.getElementById('setupSuccess');
    const enable2FA = document.getElementById('enable2FA');
    const twoFactorSetupSection = document.getElementById('twoFactorSetupSection');
    
    // Check if we should show the setup form
    checkSetupStatus();
    
    // Toggle 2FA setup section visibility
    enable2FA.addEventListener('change', function() {
        twoFactorSetupSection.style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            generateTwoFactorSetup();
        }
    });
    
    // Copy secret key to clipboard
    document.getElementById('copySecret').addEventListener('click', function() {
        const secretKey = document.getElementById('secretKey');
        secretKey.select();
        document.execCommand('copy');
        alert('Secret key copied to clipboard');
    });
    
    setupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const adminUsername = document.getElementById('adminUsername').value;
        const adminPassword = document.getElementById('adminPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const enableTwoFactor = enable2FA.checked;
        const verificationCode = document.getElementById('verificationCode').value;
        const secretKey = document.getElementById('secretKey').value;
        
        // Reset error and success messages
        setupError.style.display = 'none';
        setupSuccess.style.display = 'none';
        
        // Validate inputs
        if (!adminUsername || !adminPassword) {
            setupError.textContent = 'Username and password are required';
            setupError.style.display = 'block';
            return;
        }
        
        if (adminPassword !== confirmPassword) {
            setupError.textContent = 'Passwords do not match';
            setupError.style.display = 'block';
            return;
        }
        
        if (enableTwoFactor && !verificationCode) {
            setupError.textContent = 'Verification code is required for 2FA setup';
            setupError.style.display = 'block';
            return;
        }
        
        // Send setup request
        fetch('/api/auth/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: adminUsername,
                password: adminPassword,
                enable2FA: enableTwoFactor,
                secretKey: enableTwoFactor ? secretKey : null,
                verificationCode: enableTwoFactor ? verificationCode : null
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setupSuccess.textContent = 'Setup completed successfully! Redirecting to login...';
                setupSuccess.style.display = 'block';
                
                // Redirect to login page after 3 seconds
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 3000);
            } else {
                setupError.textContent = data.message || 'Setup failed. Please try again.';
                setupError.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Setup error:', error);
            setupError.textContent = 'An error occurred during setup. Please try again.';
            setupError.style.display = 'block';
        });
    });
    
    function generateTwoFactorSetup() {
        // Get a new secret key from the server
        fetch('/api/auth/generate-2fa-secret', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Display secret key
                document.getElementById('secretKey').value = data.secretKey;
                
                // Generate and display QR code
                const qrCodeContainer = document.getElementById('qrCode');
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
                setupError.textContent = data.message || 'Failed to generate 2FA secret';
                setupError.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('2FA setup error:', error);
            setupError.textContent = 'An error occurred while setting up 2FA';
            setupError.style.display = 'block';
        });
    }
    
    function checkSetupStatus() {
        // Check if setup has already been completed
        fetch('/api/auth/setup-status', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.setupCompleted) {
                // Setup already done, redirect to login
                window.location.href = 'login.html';
            }
        })
        .catch(error => {
            console.error('Setup status check error:', error);
        });
    }
});
