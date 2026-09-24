// ========================================
// PASSWORD VISIBILITY TOGGLE
// ========================================

class PasswordToggle {

    constructor() {
        this.toggleButtons = document.querySelectorAll('.password-toggle');
        this.init();
    }

    init() {
        this.toggleButtons.forEach(btn => {
            btn.addEventListener('click', (e) =>
                this.togglePasswordVisibility(e)
            );
        });
    }

    togglePasswordVisibility(event) {

        event.preventDefault();

        const passwordInput =
            event.currentTarget.previousElementSibling;

        if (passwordInput && passwordInput.type) {

            const isPassword =
                passwordInput.type === 'password';

            passwordInput.type =
                isPassword ? 'text' : 'password';

            event.currentTarget.setAttribute(
                'aria-label',
                isPassword ? 'Hide password' : 'Show password'
            );
        }
    }
}


// ========================================
// FORM VALIDATION
// ========================================

class FormValidator {

    constructor(formSelector) {

        this.form = document.querySelector(formSelector);

        this.fields = {

            facultyId: {
                element: document.getElementById('faculty-id'),
                validate: (value) =>
                    this.validateFacultyId(value)
            },

            fullName: {
                element: document.getElementById('full-name'),
                validate: (value) =>
                    this.validateFullName(value)
            },

            email: {
                element: document.getElementById('email'),
                validate: (value) =>
                    this.validateEmail(value)
            },

            department: {
                element: document.getElementById('department'),
                validate: (value) =>
                    this.validateDepartment(value)
            },

            password: {
                element: document.getElementById('password'),
                validate: (value) =>
                    this.validatePassword(value)
            },

            confirmPassword: {
                element: document.getElementById('confirm-password'),
                validate: (value) =>
                    this.validateConfirmPassword(value)
            }
        };

        this.init();
    }


    init() {

        if (!this.form) return;

        // Real-time validation
        Object.values(this.fields).forEach(field => {

            if (field.element) {

                field.element.addEventListener(
                    'blur',
                    () => this.validateField(field.element)
                );

                field.element.addEventListener(
                    'input',
                    () => this.clearError(field.element)
                );
            }
        });

        // Form submission
        this.form.addEventListener(
            'submit',
            (e) => this.handleSubmit(e)
        );
    }


    // ========================================
    // FIELD VALIDATION
    // ========================================

    validateField(element) {

        const fieldKey = Object.keys(this.fields).find(
            key => this.fields[key].element === element
        );

        if (!fieldKey) return true;

        const field = this.fields[fieldKey];

        const isValid =
            field.validate(element.value.trim());

        if (!isValid) {

            this.showError(
                element,
                this.getErrorMessage(fieldKey)
            );

            return false;

        } else {

            this.clearError(element);

            return true;
        }
    }


    validateFacultyId(value) {

        if (!value) return false;

        const pattern = /^[A-Za-z0-9\-]+$/;

        return pattern.test(value) && value.length >= 3;
    }


    validateFullName(value) {

        if (!value) return false;

        return (
            value.length >= 3 &&
            /^[a-zA-Z\s.]+$/.test(value)
        );
    }


    validateEmail(value) {

        if (!value) return false;

        const pattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        return pattern.test(value);
    }


    validateDepartment(value) {

        return value && value !== '';
    }


    validatePassword(value) {

        if (!value) return false;

        return value.length >= 8;
    }


    validateConfirmPassword(value) {

        const passwordField =
            this.fields.password.element;

        if (!value) return false;

        return (
            value === passwordField.value &&
            value.length >= 8
        );
    }


    // ========================================
    // ERROR MESSAGES
    // ========================================

    getErrorMessage(fieldKey) {

        const messages = {

            facultyId:
                'Faculty ID must contain letters, numbers, or hyphens (min 3 characters)',

            fullName:
                'Full name must contain only letters and spaces (min 3 characters)',

            email:
                'Please enter a valid email address',

            department:
                'Please select a department',

            password:
                'Password must be at least 8 characters long',

            confirmPassword:
                'Passwords do not match or are too short'
        };

        return messages[fieldKey] || 'Invalid input';
    }


    showError(element, message) {

        element.classList.add('error');

        const errorElement =
            element.parentElement.querySelector(
                '.error-message'
            );

        if (errorElement) {
            errorElement.textContent = message;
        }
    }


    clearError(element) {

        element.classList.remove('error');

        const errorElement =
            element.parentElement.querySelector(
                '.error-message'
            );

        if (errorElement) {
            errorElement.textContent = '';
        }
    }


    validateAllFields() {

        let isValid = true;

        Object.values(this.fields).forEach(field => {

            if (
                field.element &&
                !this.validateField(field.element)
            ) {
                isValid = false;
            }
        });

        return isValid;
    }


    // ========================================
    // FORM SUBMISSION
    // ========================================

    handleSubmit(event) {

        event.preventDefault();

        // Validate all fields
        if (!this.validateAllFields()) {
            return;
        }

        // Prepare form data
        const formData = {

            faculty_id:
                this.fields.facultyId.element.value.trim(),

            full_name:
                this.fields.fullName.element.value.trim(),

            email:
                this.fields.email.element.value.trim(),

            department:
                this.fields.department.element.value,

            password:
                this.fields.password.element.value
        };

        console.log(
            'Sending registration:',
            formData
        );


        // ========================================
        // SEND DATA TO FLASK BACKEND
        // ========================================

        fetch(
            'http://127.0.0.1:5000/api/register',
            {
                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify(formData)
            }
        )

        .then(response => response.json())

        .then(data => {

            console.log(
                'Backend response:',
                data
            );


            // ========================================
            // REGISTRATION SUCCESS
            // ========================================

            if (data.success) {

                this.showSuccessMessage();

                setTimeout(() => {
                    window.location.href = 'v-index.html';
                }, 1500);

            } else {
                    alert(data.message);

            }

        })

        .catch(error => {

            console.error(
                'Registration error:',
                error
            );

            alert(
                'Unable to connect to backend.'
            );
        });
    }


    // ========================================
    // CLEAR ALL ERRORS
    // ========================================

    clearAllErrors() {

        Object.values(this.fields).forEach(field => {

            if (field.element) {

                this.clearError(
                    field.element
                );
            }
        });
    }


    // ========================================
    // SUCCESS MESSAGE
    // ========================================

    showSuccessMessage() {

        const successMsg =
            document.createElement('div');

        successMsg.className =
            'success-message';

        successMsg.textContent =
            'Registration submitted successfully!';


        successMsg.style.cssText = `

            position: fixed;

            top: 2rem;

            left: 50%;

            transform: translateX(-50%);

            background-color: var(--accent-success);

            color: white;

            padding: 1rem 2rem;

            border-radius: 6px;

            box-shadow: var(--shadow-md);

            z-index: 999;

            animation:
                slideDown 0.3s ease-out,
                slideUp 0.3s ease-in 1.5s forwards;
        `;


        document.body.appendChild(
            successMsg
        );


        setTimeout(() => {

            successMsg.remove();

        }, 2000);
    }
}


// ========================================
// INITIALIZATION
// ========================================

document.addEventListener(
    'DOMContentLoaded',
    () => {

        // Initialize password toggle
        new PasswordToggle();

        // Initialize form validator
        new FormValidator(
            '#registration-form'
        );


        // ========================================
        // SUCCESS MESSAGE ANIMATION
        // ========================================

        const style =
            document.createElement('style');

        style.textContent = `

            @keyframes slideDown {

                from {
                    opacity: 0;

                    transform:
                        translateX(-50%)
                        translateY(-20px);
                }

                to {
                    opacity: 1;

                    transform:
                        translateX(-50%)
                        translateY(0);
                }
            }


            @keyframes slideUp {

                to {
                    opacity: 0;

                    transform:
                        translateX(-50%)
                        translateY(-20px);
                }
            }


            @media (prefers-reduced-motion: reduce) {

                .success-message {
                    animation: none !important;
                    opacity: 0;
                }
            }
        `;

        document.head.appendChild(style);
    }
);