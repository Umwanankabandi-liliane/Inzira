package com.inzira.app;

import android.content.Context;
import android.content.SharedPreferences;

public final class InziraPrefs {

    public static final String PREFS_NAME = "inzira_prefs";
    public static final String KEY_LANGUAGE = "language";
    public static final String KEY_LANGUAGE_CHOSEN = "language_chosen";
    public static final String KEY_DISTRICT = "district";
    public static final String KEY_AGE = "age";
    public static final String KEY_EDUCATION = "education";
    public static final String KEY_INTERESTS = "interests";
    public static final String KEY_SKILLS = "skills";
    public static final String KEY_PROFILE_COMPLETE = "profile_complete";
    public static final String KEY_PRIVACY_SHARE_ANON = "privacy_share_anon";
    public static final String KEY_PRIVACY_PERSONAL_NOTIF = "privacy_personal_notif";
    public static final String KEY_PRIVACY_USAGE_ANALYTICS = "privacy_usage_analytics";

    public static final String KEY_RESET_EMAIL = "reset_email";
    public static final String KEY_RESET_CODE = "reset_code";
    public static final String KEY_RESET_TS = "reset_ts";
    public static final String KEY_BACKEND_URL = "backend_url";
    public static final String KEY_MIFOTRA_TOKEN = "mifotra_token";
    public static final String KEY_MIFOTRA_EXPIRY = "mifotra_expiry";
    public static final String ENGLISH = "english";
    public static final String KINYARWANDA = "kinyarwanda";

    private InziraPrefs() {
    }

    public static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public static String getLanguage(Context context) {
        return prefs(context).getString(KEY_LANGUAGE, ENGLISH);
    }

    public static void setLanguage(Context context, String language) {
        prefs(context).edit().putString(KEY_LANGUAGE, language).apply();
    }

    public static boolean hasChosenLanguage(Context context) {
        return prefs(context).getBoolean(KEY_LANGUAGE_CHOSEN, false);
    }

    public static void setLanguageChosen(Context context, boolean chosen) {
        prefs(context).edit().putBoolean(KEY_LANGUAGE_CHOSEN, chosen).apply();
    }

    public static String getEducation(Context context) {
        return prefs(context).getString(KEY_EDUCATION, "");
    }

    public static void setEducation(Context context, String education) {
        prefs(context).edit().putString(KEY_EDUCATION, education != null ? education : "").apply();
    }

    public static String getInterests(Context context) {
        return prefs(context).getString(KEY_INTERESTS, "");
    }

    public static void setInterests(Context context, String interests) {
        prefs(context).edit().putString(KEY_INTERESTS, interests != null ? interests : "").apply();
    }

    public static String getSkills(Context context) {
        return prefs(context).getString(KEY_SKILLS, "");
    }

    public static void setSkills(Context context, String skills) {
        prefs(context).edit().putString(KEY_SKILLS, skills != null ? skills : "").apply();
    }

    public static boolean isProfileComplete(Context context) {
        return prefs(context).getBoolean(KEY_PROFILE_COMPLETE, false);
    }

    public static void setProfileComplete(Context context, boolean complete) {
        prefs(context).edit().putBoolean(KEY_PROFILE_COMPLETE, complete).apply();
    }

    public static boolean isKinyarwanda(Context context) {
        return KINYARWANDA.equals(getLanguage(context));
    }

    public static String displayLanguage(Context context) {
        return isKinyarwanda(context) ? "Kinyarwanda" : "English";
    }

    public static String getDistrict(Context context) {
        return prefs(context).getString(KEY_DISTRICT, "");
    }

    public static void setDistrict(Context context, String district) {
        prefs(context).edit().putString(KEY_DISTRICT, district != null ? district : "").apply();
    }

    public static String getAge(Context context) {
        return prefs(context).getString(KEY_AGE, "");
    }

    public static void setAge(Context context, String age) {
        prefs(context).edit().putString(KEY_AGE, age != null ? age : "").apply();
    }

    public static boolean hasDistrict(Context context) {
        String d = getDistrict(context);
        return d != null && !d.isEmpty() && !d.startsWith("Select");
    }

    public static void setMifotraSession(Context context, String token, long expiryEpochMs) {
        prefs(context).edit()
                .putString(KEY_MIFOTRA_TOKEN, token)
                .putLong(KEY_MIFOTRA_EXPIRY, expiryEpochMs)
                .apply();
    }

    public static String getMifotraToken(Context context) {
        return prefs(context).getString(KEY_MIFOTRA_TOKEN, "");
    }

    public static boolean isMifotraSessionValid(Context context) {
        String token = getMifotraToken(context);
        if (token == null || token.isEmpty()) {
            return false;
        }
        return System.currentTimeMillis() < prefs(context).getLong(KEY_MIFOTRA_EXPIRY, 0L);
    }

    public static void clearMifotraSession(Context context) {
        prefs(context).edit()
                .remove(KEY_MIFOTRA_TOKEN)
                .remove(KEY_MIFOTRA_EXPIRY)
                .apply();
    }

    public static boolean getShareAnonymizedSearch(Context context) {
        return prefs(context).getBoolean(KEY_PRIVACY_SHARE_ANON, true);
    }

    public static void setShareAnonymizedSearch(Context context, boolean enabled) {
        prefs(context).edit().putBoolean(KEY_PRIVACY_SHARE_ANON, enabled).apply();
    }

    public static boolean getPersonalizedNotifications(Context context) {
        return prefs(context).getBoolean(KEY_PRIVACY_PERSONAL_NOTIF, true);
    }

    public static void setPersonalizedNotifications(Context context, boolean enabled) {
        prefs(context).edit().putBoolean(KEY_PRIVACY_PERSONAL_NOTIF, enabled).apply();
    }

    public static boolean getUsageAnalytics(Context context) {
        return prefs(context).getBoolean(KEY_PRIVACY_USAGE_ANALYTICS, false);
    }

    public static void setUsageAnalytics(Context context, boolean enabled) {
        prefs(context).edit().putBoolean(KEY_PRIVACY_USAGE_ANALYTICS, enabled).apply();
    }

    public static void setResetSession(Context context, String email, String code, long tsMs) {
        prefs(context).edit()
                .putString(KEY_RESET_EMAIL, email != null ? email : "")
                .putString(KEY_RESET_CODE, code != null ? code : "")
                .putLong(KEY_RESET_TS, tsMs)
                .apply();
    }

    public static String getResetEmail(Context context) {
        return prefs(context).getString(KEY_RESET_EMAIL, "");
    }

    public static String getResetCode(Context context) {
        return prefs(context).getString(KEY_RESET_CODE, "");
    }

    public static long getResetTs(Context context) {
        return prefs(context).getLong(KEY_RESET_TS, 0L);
    }

    public static String getBackendUrl(Context context) {
        return prefs(context).getString(KEY_BACKEND_URL, "");
    }

    public static void setBackendUrl(Context context, String url) {
        prefs(context).edit().putString(KEY_BACKEND_URL, url != null ? url : "").apply();
    }
}
