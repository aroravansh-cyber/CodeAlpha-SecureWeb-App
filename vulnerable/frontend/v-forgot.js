/* ========================================
   Faculty Secure Portal
   Forgot Password
======================================== */

const forgotForm = document.getElementById("forgotForm");
const otpForm = document.getElementById("otpForm");
const resetPasswordForm = document.getElementById("resetPasswordForm");

const emailInput = document.getElementById("email");
const otpInput = document.getElementById("otp");
const newPasswordInput = document.getElementById("newPassword");
const confirmPasswordInput = document.getElementById("confirmPassword");

const emailStep = document.getElementById("emailStep");
const otpStep = document.getElementById("otpStep");
const passwordStep = document.getElementById("passwordStep");

const message = document.getElementById("message");

let userEmail = "";


/* ========================================
   STEP 1 - SEND OTP
======================================== */

forgotForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email = emailInput.value.trim();

    clearMessage();

    if (!email) {
        showMessage("Please enter your registered email.", "error");
        return;
    }

    if (!isValidEmail(email)) {
        showMessage("Please enter a valid email address.", "error");
        return;
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/api/forgot-password",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            userEmail = email;

            emailStep.style.display = "none";
            otpStep.style.display = "block";

            showMessage(
                data.message || "OTP sent successfully.",
                "success"
            );

            otpInput.focus();

        } else {

            showMessage(
                data.message || "No account was found with this email.",
                "error"
            );
        }

    } catch (error) {

        console.error("Send OTP error:", error);

        showMessage(
            "Unable to connect to the server. Please try again.",
            "error"
        );
    }
});


/* ========================================
   STEP 2 - VERIFY OTP
======================================== */

otpForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const otp = otpInput.value.trim();

    clearMessage();

    if (!otp) {
        showMessage("Please enter the OTP.", "error");
        return;
    }

    if (!/^\d{6}$/.test(otp)) {
        showMessage("OTP must be 6 digits.", "error");
        return;
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/api/verify-otp",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: userEmail,
                    otp: otp
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            otpStep.style.display = "none";
            passwordStep.style.display = "block";

            showMessage(
                data.message || "OTP verified successfully.",
                "success"
            );

            newPasswordInput.focus();

        } else {

            showMessage(
                data.message || "Invalid or expired OTP.",
                "error"
            );
        }

    } catch (error) {

        console.error("OTP verification error:", error);

        showMessage(
            "Unable to connect to the server. Please try again.",
            "error"
        );
    }
});


/* ========================================
   STEP 3 - RESET PASSWORD
======================================== */

resetPasswordForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        clearMessage();

        if (!newPassword || !confirmPassword) {

            showMessage(
                "Please fill in both password fields.",
                "error"
            );

            return;
        }

        if (newPassword.length < 6) {

            showMessage(
                "Password must be at least 6 characters long.",
                "error"
            );

            return;
        }

        if (newPassword !== confirmPassword) {

            showMessage(
                "Passwords do not match.",
                "error"
            );

            return;
        }

        try {

            const response = await fetch(
                "http://127.0.0.1:5000/api/reset-password",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: userEmail,
                        password: newPassword
                    })
                }
            );

            const data = await response.json();

            if (response.ok) {

                showMessage(
                    data.message || "Password reset successfully.",
                    "success"
                );

                resetPasswordForm.reset();

                setTimeout(function () {
                    window.location.href = "index.html";
                }, 1500);

            } else {

                showMessage(
                    data.message || "Unable to reset password.",
                    "error"
                );
            }

        } catch (error) {

            console.error("Password reset error:", error);

            showMessage(
                "Unable to connect to the server. Please try again.",
                "error"
            );
        }
    }
);


/* ========================================
   EMAIL VALIDATION
======================================== */

function isValidEmail(email) {

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}


/* ========================================
   MESSAGE
======================================== */

function showMessage(text, type) {

    message.textContent = text;
    message.className = `message ${type}`;
}


function clearMessage() {

    message.textContent = "";
    message.className = "message";
}