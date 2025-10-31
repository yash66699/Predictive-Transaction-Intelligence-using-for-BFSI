// Replace the entire loginForm event listener with this:
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = document.getElementById('emailLogin').value;
    const password = document.getElementById('passwordLogin').value;
    const pin = document.getElementById('pinLogin').value;

    // Basic validation
    if (!email || !password || !pin) {
        const form = document.getElementById('loginForm');
        form.classList.add('shake');
        setTimeout(() => form.classList.remove('shake'), 450);
        alert("Please fill in all fields!");
        return;
    }

    if (!/^[0-9]{4}$/.test(pin)) {
        document.getElementById('pinErrorLogin').style.display = "block";
        return;
    } else {
        document.getElementById('pinErrorLogin').style.display = "none";
    }

    try {
        // Add loading state
        const loginButton = document.querySelector('#loginForm .btn');
        loginButton.classList.add('loading');
        loginButton.textContent = 'Logging in...';
        
        // Demo authentication (bypass Firebase)
        console.log('Demo login with:', { email, pin });
        
        // Show loading animation
        showLoginLoading();
        
        // Store demo user data
        const firstName = email.split('@')[0] || 'User';
        localStorage.setItem('userFirstName', firstName);
        localStorage.setItem('userEmail', email);
        localStorage.setItem('userMobile', '1234567890');
        localStorage.setItem('userCountryCode', '+1');
        localStorage.setItem('userLastName', 'Demo');
        
        // Success - redirect to dashboard
        setTimeout(() => {
            window.location.href = '../dashboard/dashboard.html';
        }, 1500);
        
    } catch (error) {
        console.error('Login Error:', error);
        alert("Demo login successful! Redirecting...");
        
        // Even on "error", proceed to demo (for testing)
        showLoginLoading();
        setTimeout(() => {
            window.location.href = '../dashboard/dashboard.html';
        }, 1500);
    }
});