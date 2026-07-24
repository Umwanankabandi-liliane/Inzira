package com.inzira.app;

import android.content.Context;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.FirebaseDatabase;

public final class SessionManager {

    private SessionManager() {
    }

    public static boolean isLoggedIn(Context context) {
        if (FirebaseUtil.currentUser() != null) {
            return true;
        }
        return LocalAuthStore.isLoggedIn(context);
    }

    public static boolean usesFirebase() {
        return FirebaseUtil.currentUser() != null;
    }

    public static String getEmail(Context context) {
        FirebaseUser user = FirebaseUtil.currentUser();
        if (user != null && user.getEmail() != null) {
            return user.getEmail();
        }
        return LocalAuthStore.getEmail(context);
    }

    public static String getFirstName(Context context) {
        FirebaseUser user = FirebaseUtil.currentUser();
        if (user != null) {
            String display = user.getDisplayName();
            if (display != null && !display.trim().isEmpty()) {
                return display.trim().split("\\s+")[0];
            }
            String email = user.getEmail();
            if (email != null && email.contains("@")) {
                return email.substring(0, email.indexOf('@'));
            }
        }
        return LocalAuthStore.getFirstName(context);
    }

    public static void signOut(Context context) {
        FirebaseAuth auth = FirebaseUtil.auth();
        if (auth != null) {
            auth.signOut();
        }
        LocalAuthStore.clearAccount(context);
    }

    public static void syncFirebaseProfile(Context context) {
        FirebaseUser user = FirebaseUtil.currentUser();
        if (user == null) {
            return;
        }
        FirebaseDatabase.getInstance().getReference("users")
                .child(user.getUid())
                .get()
                .addOnSuccessListener(snapshot -> {
                    String language = snapshot.child("language").getValue(String.class);
                    String district = snapshot.child("district").getValue(String.class);
                    if (language != null && !language.isEmpty()) {
                        InziraPrefs.setLanguage(context, language);
                    }
                    if (district != null && !district.isEmpty()) {
                        InziraPrefs.setDistrict(context, district);
                    }
                });
    }
}
