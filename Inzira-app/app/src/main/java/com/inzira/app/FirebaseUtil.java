package com.inzira.app;

import com.google.firebase.FirebaseApp;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;

public final class FirebaseUtil {

    private FirebaseUtil() {
    }

    public static boolean isConfigured() {
        try {
            FirebaseApp.getInstance();
            return true;
        } catch (IllegalStateException e) {
            return false;
        }
    }

    public static FirebaseAuth auth() {
        if (!isConfigured()) {
            return null;
        }
        return FirebaseAuth.getInstance();
    }

    public static FirebaseUser currentUser() {
        FirebaseAuth auth = auth();
        return auth != null ? auth.getCurrentUser() : null;
    }
}
