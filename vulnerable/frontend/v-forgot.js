/* ========================================
   Faculty Secure Portal
   Forgot Password
======================================== */

const forgotForm = document.getElementById("forgotForm");
const emailInput = document.getElementById("email");
const message = document.getElementById("message");


forgotForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email = emailInput.value.trim();

    // Clear previous message
    message.className = "message";
    message.textContent = "";

    if (!email) {
        showMessage("Please enter your registered email.", "error");
        return;
    }

    try {

        const response = await fetch("http://127.0.0.1:5000/api/forgot-password", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email
            })
        });


        const data = await response.json();


        if (response.ok) {

            showMessage(
                data.message || "Account found. Password reset can continue.",
                "success"
            );

        } else {

            showMessage(
                data.message || "No faculty account was found with this email.",
                "error"
            );

        }

    } catch (error) {

        console.error("Forgot password error:", error);

        showMessage(
            "Unable to connect to the server. Please try again.",
            "error"
        );
    }

});


function showMessage(text, type) {

    message.textContent = text;

    message.className = `message ${type}`;
}

