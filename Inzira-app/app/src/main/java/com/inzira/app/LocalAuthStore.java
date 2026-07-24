package com.inzira.app;

import android.content.Context;

/**
 * Local account storage — works without Firebase for demos and development.
 * When google-services.json is added, Firebase auth takes priority.
 */
public final class LocalAuthStore {

    private static final String KEY_NAME = "local_user_name";
    private static final String KEY_EMAIL = "local_user_email";
    private static final String KEY_PASSWORD = "local_user_password";
    private static final String KEY_LOGGED_IN = "local_logged_in";

    private LocalAuthStore() {
    }

    public static boolean hasAccount(Context context) {
        String email = InziraPrefs.prefs(context).getString(KEY_EMAIL, "");
        return email != null && !email.isEmpty();
    }

    public static boolean isLoggedIn(Context context) {
        return InziraPrefs.prefs(context).getBoolean(KEY_LOGGED_IN, false) && hasAccount(context);
    }

    public static void register(Context context, String name, String email, String password, String district) {
        InziraPrefs.prefs(context).edit()
                .putString(KEY_NAME, name.trim())
                .putString(KEY_EMAIL, email.trim().toLowerCase())
                .putString(KEY_PASSWORD, password)
                .putBoolean(KEY_LOGGED_IN, true)
                .apply();
        InziraPrefs.setDistrict(context, district);
    }

    public static boolean login(Context context, String email, String password) {
        String savedEmail = InziraPrefs.prefs(context).getString(KEY_EMAIL, "");
        String savedPassword = InziraPrefs.prefs(context).getString(KEY_PASSWORD, "");
        if (savedEmail == null || savedEmail.isEmpty()) {
            return false;
        }
        boolean ok = savedEmail.equalsIgnoreCase(email.trim())
                && savedPassword != null
                && savedPassword.equals(password);
        if (ok) {
            InziraPrefs.prefs(context).edit().putBoolean(KEY_LOGGED_IN, true).apply();
        }
        return ok;
    }

    public static void logout(Context context) {
        InziraPrefs.prefs(context).edit().putBoolean(KEY_LOGGED_IN, false).apply();
    }

    public static String getName(Context context) {
        return InziraPrefs.prefs(context).getString(KEY_NAME, "");
    }

    public static String getEmail(Context context) {
        return InziraPrefs.prefs(context).getString(KEY_EMAIL, "");
    }

    public static String getFirstName(Context context) {
        String name = getName(context);
        if (name == null || name.trim().isEmpty()) {
            return "";
        }
        return name.trim().split("\\s+")[0];
    }

    public static void clearAccount(Context context) {
        InziraPrefs.prefs(context).edit()
                .remove(KEY_NAME)
                .remove(KEY_EMAIL)
                .remove(KEY_PASSWORD)
                .remove(KEY_LOGGED_IN)
                .apply();
    }

    public static boolean resetPassword(Context context, String email, String newPassword) {
        String savedEmail = InziraPrefs.prefs(context).getString(KEY_EMAIL, "");
        if (savedEmail == null || savedEmail.isEmpty() || email == null) {
            return false;
        }
        if (!savedEmail.equalsIgnoreCase(email.trim())) {
            return false;
        }
        InziraPrefs.prefs(context).edit().putString(KEY_PASSWORD, newPassword).apply();
        return true;
    }
}
