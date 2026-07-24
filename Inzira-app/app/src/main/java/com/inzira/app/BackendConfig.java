package com.inzira.app;

import android.content.Context;

/**
 * API base URL for the FastAPI backend (search, assistant, MIFOTRA dashboard).
 * Release builds default to BuildConfig.API_BASE_URL (set INZIRA_API_URL in gradle.properties).
 * Debug builds default to emulator host 10.0.2.2:8000.
 * Users can override in Settings → Server connection.
 */
public final class BackendConfig {

    private BackendConfig() {
    }

    public static String getBaseUrl(Context context) {
        String saved = InziraPrefs.getBackendUrl(context);
        if (saved == null || saved.trim().isEmpty()) {
            return BuildConfig.API_BASE_URL;
        }
        return normalize(saved);
    }

    public static void setBaseUrl(Context context, String url) {
        InziraPrefs.setBackendUrl(context, normalize(url));
        RetrofitClient.reset();
    }

    public static void resetToDefault(Context context) {
        InziraPrefs.setBackendUrl(context, "");
        RetrofitClient.reset();
    }

    public static String displayUrl(Context context) {
        String url = getBaseUrl(context);
        if (url.endsWith("/")) {
            return url.substring(0, url.length() - 1);
        }
        return url;
    }

    public static String webAppUrl(Context context) {
        return displayUrl(context) + "/#/home";
    }

    static String normalize(String url) {
        if (url == null) {
            return BuildConfig.API_BASE_URL;
        }
        String trimmed = url.trim();
        if (trimmed.isEmpty()) {
            return BuildConfig.API_BASE_URL;
        }
        if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) {
            trimmed = "https://" + trimmed;
        }
        if (!trimmed.endsWith("/")) {
            trimmed = trimmed + "/";
        }
        return trimmed;
    }
}
