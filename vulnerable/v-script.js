/* ========================================
   Teacher Secure Portal - JavaScript
   Vulnerable Version for CodeAlpha Auditing
   ======================================== */

// ========================================
// Form and Element References
// ========================================

const loginForm = document.getElementById('loginForm');
const teacherIdInput = document.getElementById('teacherId');
const passwordInput = document.getElementById('password');
const passwordToggle = document.getElementById('passwordToggle');
const captchaAnswerInput = document.getElementById('captchaAnswer');
const signInBtn = document.getElementById('signInBtn');
const rememberMeCheckbox = document.getElementById('rememberMe');

// Error message elements
const teacherIdError = document.getElementById('teacherIdError');
const passwordError = document.getElementById('passwordError');
const captchaError = document.getElementById('captchaError');

// CAPTCHA correct answer (7 + 4 = 11)
const CAPTCHA_ANSWER = 11;

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

function validateTeacherId(value) {
    if (!value || value.trim() === '') {
        return 'Teacher ID or email is required';
    }
    if (value.trim().length < 3) {
        return 'Teacher ID or email must be at least 3 characters';
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

function validateCaptcha(value) {
    if (!value || value.trim() === '') {
        return 'Security answer is required';
    }
    
    const numValue = parseInt(value, 10);
    if (isNaN(numValue)) {
        return 'Please enter a valid number';
    }
    
    if (numValue !== CAPTCHA_ANSWER) {
        return 'Incorrect answer. Please try again.';
    }
    
    return '';
}

// ========================================
// Real-time Validation
// ========================================

teacherIdInput.addEventListener('blur', function() {
    const error = validateTeacherId(this.value);
    displayError(this, error, teacherIdError);
});

teacherIdInput.addEventListener('input', function() {
    if (this.classList.contains('error')) {
        const error = validateTeacherId(this.value);
        displayError(this, error, teacherIdError);
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

captchaAnswerInput.addEventListener('blur', function() {
    const error = validateCaptcha(this.value);
    displayError(this, error, captchaError);
});

captchaAnswerInput.addEventListener('input', function() {
    if (this.classList.contains('error')) {
        const error = validateCaptcha(this.value);
        displayError(this, error, captchaError);
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
    teacherIdInput.classList.remove('error');
    passwordInput.classList.remove('error');
    captchaAnswerInput.classList.remove('error');
    
    teacherIdError.textContent = '';
    passwordError.textContent = '';
    captchaError.textContent = '';
}

// ========================================
// Form Submission Handler
// ========================================

loginForm.addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Clear previous errors
    clearAllErrors();
    
    // Validate all fields
    const teacherIdVal = teacherIdInput.value;
    const passwordVal = passwordInput.value;
    const captchaVal = captchaAnswerInput.value;
    
    const teacherIdErr = validateTeacherId(teacherIdVal);
    const passwordErr = validatePassword(passwordVal);
    const captchaErr = validateCaptcha(captchaVal);
    
    // Display any errors
    if (teacherIdErr) displayError(teacherIdInput, teacherIdErr, teacherIdError);
    if (passwordErr) displayError(passwordInput, passwordErr, passwordError);
    if (captchaErr) displayError(captchaAnswerInput, captchaErr, captchaError);
    
    // If there are validation errors, don't proceed
    if (teacherIdErr || passwordErr || captchaErr) {
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
    setTimeout(function() {
        // In a real scenario, the browser would handle form submission
        // For now, we show the loading state briefly
        // The actual submission depends on backend availability
        
        // Note: In development, if no backend is running,
        // the browser will handle this based on the form's action attribute
        loginForm.submit();
    }, 500);
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
// CAPTCHA Reset (Optional Enhancement)
// ========================================

// You could add a button to regenerate CAPTCHA questions in the future
// For now, the CAPTCHA question remains static (7 + 4 = ?)

function resetCaptcha() {
    captchaAnswerInput.value = '';
    captchaError.textContent = '';
    captchaAnswerInput.classList.remove('error');
    captchaAnswerInput.focus();
}

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