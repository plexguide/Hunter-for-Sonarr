document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginError = document.getElementById('loginError');
    
    // Check if user is already logged in
    checkAuthStatus();
    
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const twoFactorCode = document.getElementById('twoFactorCode').value;
        
        // Reset error message
        loginError.style.display = 'none';
        
        // First check if 2FA is required
        fetch('/api/auth/check-2fa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username })
        })
        .then(response => response.json())
        .then(data => {
            if (data.requires2FA && !twoFactorCode) {
                // Show 2FA input field
                document.getElementById('twoFactorGroup').style.display = 'block';
                loginError.textContent = 'Please enter your 2FA code';
                loginError.style.display = 'block';
            } else {
                // Proceed with login
                attemptLogin(username, password, twoFactorCode);
            }
        })
        .catch(error => {
            console.error('Error checking 2FA requirement:', error);
            loginError.textContent = 'An error occurred. Please try again.';
            loginError.style.display = 'block';
        });
    });
    
    function attemptLogin(username, password, twoFactorCode) {
        fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                username, 
                password,
                twoFactorCode: twoFactorCode || ''
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Login failed');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Store the auth token in localStorage
                localStorage.setItem('huntarr_token', data.token);
                localStorage.setItem('huntarr_username', username);
                
                // Redirect to main page
                window.location.href = '/';
            } else {
                loginError.textContent = data.message || 'Invalid username or password';
                loginError.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            loginError.textContent = 'Invalid username or password';
            loginError.style.display = 'block';
        });
    }
    
    function checkAuthStatus() {
        const token = localStorage.getItem('huntarr_token');
        if (token) {
            // Verify token validity
            fetch('/api/auth/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
            .then(response => {
                if (response.ok) {
                    // Token is valid, redirect to dashboard
                    window.location.href = '/';
                } else {
                    // Token is invalid, clear it
                    localStorage.removeItem('huntarr_token');
                    localStorage.removeItem('huntarr_username');
                }
            })
            .catch(error => {
                console.error('Token verification error:', error);
                localStorage.removeItem('huntarr_token');
                localStorage.removeItem('huntarr_username');
            });
        }
    }
});
