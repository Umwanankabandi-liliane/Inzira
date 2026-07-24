package com.inzira.app;

import com.google.firebase.auth.FirebaseAuthInvalidCredentialsException;
import com.google.firebase.auth.FirebaseAuthInvalidUserException;
import com.google.firebase.auth.FirebaseAuthUserCollisionException;
import com.google.firebase.auth.FirebaseAuthWeakPasswordException;

public final class FirebaseAuthHelper {

    private FirebaseAuthHelper() {
    }

    /** True when google-services.json is present and Firebase is initialized. */
    public static boolean isEnabled() {
        return FirebaseUtil.isConfigured() && FirebaseUtil.auth() != null;
    }

    public static String loginErrorMessage(Exception e) {
        if (e instanceof FirebaseAuthInvalidUserException) {
            return "No account found for this email. Tap Create account below.";
        }
        if (e instanceof FirebaseAuthInvalidCredentialsException) {
            return "Wrong email or password.";
        }
        String msg = e.getMessage();
        if (msg != null) {
            String lower = msg.toLowerCase();
            if (lower.contains("password") && lower.contains("invalid")) {
                return "Wrong email or password.";
            }
            if (lower.contains("no user record") || lower.contains("user not found")) {
                return "No account found for this email. Tap Create account below.";
            }
            if (lower.contains("network")) {
                return "Network error. Check your connection and try again.";
            }
            if (lower.contains("too many")) {
                return "Too many attempts. Please wait a moment and try again.";
            }
        }
        return "Sign in failed. Check your email and password.";
    }

    public static String registerErrorMessage(Exception e) {
        if (e instanceof FirebaseAuthUserCollisionException) {
            return "This email is already registered. Sign in instead.";
        }
        if (e instanceof FirebaseAuthWeakPasswordException) {
            return "Password is too weak. Use at least 6 characters.";
        }
        if (e instanceof FirebaseAuthInvalidCredentialsException) {
            return "Invalid email address.";
        }
        String msg = e.getMessage();
        if (msg != null && msg.toLowerCase().contains("network")) {
            return "Network error. Check your connection and try again.";
        }
        return "Registration failed. Try again or use a different email.";
    }

    public static String resetErrorMessage(Exception e) {
        if (e instanceof FirebaseAuthInvalidUserException) {
            return "No account found for this email.";
        }
        return "Could not send reset email. Check the address and try again.";
    }

    public static boolean isValidEmail(String email) {
        return email != null
                && email.contains("@")
                && email.indexOf('@') > 0
                && email.indexOf('@') < email.length() - 1;
    }
}
