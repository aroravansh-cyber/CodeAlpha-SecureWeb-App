/* ========================================
   faculity Secure Portal - JavaScript
   Vulnerable Version for CodeAlpha Auditing
   ======================================== */

// ========================================
// Form and Element References
// ========================================

const loginForm = document.getElementById('loginForm');
const faculityIdInput = document.getElementById('faculityId');
const passwordInput = document.getElementById('password');
const passwordToggle = document.getElementById('passwordToggle');
const signInBtn = document.getElementById('signInBtn');
const rememberMeCheckbox = document.getElementById('rememberMe');

// Error message elements
const faculityIdError = document.getElementById('faculityIdError');
const passwordError = document.getElementById('passwordError');


// ========================================
// Password Show/Hide Toggle
// ========================================

passwordToggle.addEventListener('click', togglePasswordVisibility);
passwordToggle.addEventListener('keydown', function(event) {
    // Allow Enter or Space to toggle password
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        togglePasswordVisibility();
    }
});

function togglePasswordVisibility() {
    const isPassword = passwordInput.type === 'password';
    
    if (isPassword) {
        passwordInput.type = 'text';
        passwordToggle.setAttribute('aria-label', 'Hide password');
    } else {
        passwordInput.type = 'password';
        passwordToggle.setAttribute('aria-label', 'Show password');
    }
}

// ========================================
// Form Validation
// ========================================

function validatefaculityId(value) {
    if (!value || value.trim() === '') {
        return 'faculity ID or email is required';
    }
    if (value.trim().length < 3) {
        return 'faculity ID or email must be at least 3 characters';
    }
    return '';
}

function validatePassword(value) {
    if (!value || value.trim() === '') {
        return 'Password is required';
    }
    if (value.length < 6) {
        return 'Password must be at least 6 characters';
    }
    return '';
}


// ========================================
// Real-time Validation
// ========================================

faculityIdInput.addEventListener('blur', function() {
    const error = validatefaculityId(this.value);
    displayError(this, error, faculityIdError);
});

faculityIdInput.addEventListener('input', function() {
    if (this.classList.contains('error')) {
        const error = validatefaculityId(this.value);
        displayError(this, error, faculityIdError);
    }
});

passwordInput.addEventListener('blur', function() {
    const error = validatePassword(this.value);
    displayError(this, error, passwordError);
});

passwordInput.addEventListener('input', function() {
    if (this.classList.contains('error')) {
        const error = validatePassword(this.value);
        displayError(this, error, passwordError);
    }
});

// ========================================
// Error Display Helper
// ========================================

function displayError(inputElement, errorMessage, errorElement) {
    if (errorMessage) {
        inputElement.classList.add('error');
        errorElement.textContent = errorMessage;
    } else {
        inputElement.classList.remove('error');
        errorElement.textContent = '';
    }
}

// ========================================
// Clear All Errors
// ========================================

function clearAllErrors() {
    faculityIdInput.classList.remove('error');
    passwordInput.classList.remove('error');
    
    faculityIdError.textContent = '';
    passwordError.textContent = '';
}

// ========================================
// Form Submission Handler
// ========================================

loginForm.addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Clear previous errors
    clearAllErrors();
    
    // Validate all fields
    const faculityIdVal = faculityIdInput.value;
    const passwordVal = passwordInput.value;
  
    const faculityIdErr = validatefaculityId(faculityIdVal);
    const passwordErr = validatePassword(passwordVal);
    
    // Display any errors
    if (faculityIdErr) displayError(faculityIdInput, faculityIdErr, faculityIdError);
    if (passwordErr) displayError(passwordInput, passwordErr, passwordError);
    
    // If there are validation errors, don't proceed
    if (faculityIdErr || passwordErr) {
        return;
    }
    
    // ========================================
    // IMPORTANT: NO FAKE AUTHENTICATION
    // ========================================
    // This frontend does NOT:
    // - Hardcode credentials
    // - Store passwords anywhere
    // - Fake a successful login
    // - Redirect to dashboard as if authenticated
    //
    // The actual authentication is handled by the Flask backend.
    // This form submission will be sent to the backend for real verification.
    // ========================================
    
    // Set button to loading state
    showLoadingState();
    
    // Submit the form to the backend
    // The action attribute is set to "/login" in the HTML
    // This will be a POST request to the Flask backend
    fetch("http://127.0.0.1:5000/api/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            faculty_id: faculityIdVal,
            password: passwordVal
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingState();

        if (data.success) {
            alert("Login successful!");
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        hideLoadingState();
        console.error("Backend error:", error);
        alert("Unable to connect to backend.");
    });
});

// ========================================
// Loading State
// ========================================

function showLoadingState() {
    signInBtn.disabled = true;
    signInBtn.classList.add('loading');
    signInBtn.textContent = '';
}

function hideLoadingState() {
    signInBtn.disabled = false;
    signInBtn.classList.remove('loading');
    signInBtn.textContent = 'Sign In';
}

// Reset loading state if user returns to page after form submission
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        hideLoadingState();
    }
});

// ========================================
// Accessibility: Focus Management
// ========================================

// Improve tab order and focus visibility
document.addEventListener('keydown', function(event) {
    // If user presses Tab, ensure focus is managed
    if (event.key === 'Tab') {
        // Browser handles this by default, but we ensure focus styles are visible
        document.body.classList.add('keyboard-nav');
    }
});

document.addEventListener('mousedown', function() {
    // Remove keyboard-nav class when user uses mouse
    document.body.classList.remove('keyboard-nav');
});

// ========================================
// Form Reset on Page Load
// ========================================

// Clear form fields on page load (security best practice)
window.addEventListener('load', function() {
    loginForm.reset();
    // Restore password input type to 'password'
    if (passwordInput.type === 'text') {
        passwordInput.type = 'password';
        passwordToggle.setAttribute('aria-label', 'Show password');
    }
});

// ========================================
// Console Warning
// ========================================

console.warn('SECURITY NOTICE: This is the vulnerable frontend version for CodeAlpha auditing. Do not use in production.');