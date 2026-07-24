package com.inzira.app;

import android.content.Context;
import android.util.Log;
import com.google.firebase.auth.FirebaseAuth;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public final class BackendSyncHelper {

    private static final String TAG = "BackendSyncHelper";

    private BackendSyncHelper() {
    }

    public static void saveSite(Context context, String url, String title, String category, boolean notifyEnabled) {
        if (FirebaseAuth.getInstance().getCurrentUser() == null || url == null || url.isEmpty()) {
            return;
        }
        SavedSiteBody body = new SavedSiteBody(url, title, category, notifyEnabled);
        RetrofitClient.getApiService().saveSite(body).enqueue(new Callback<java.util.Map<String, Object>>() {
            @Override
            public void onResponse(Call<java.util.Map<String, Object>> call, Response<java.util.Map<String, Object>> response) {
                if (!response.isSuccessful()) {
                    Log.w(TAG, "saveSite failed: " + response.code());
                }
            }

            @Override
            public void onFailure(Call<java.util.Map<String, Object>> call, Throwable t) {
                Log.w(TAG, "saveSite error", t);
            }
        });
    }

    public static void removeSite(Context context, String domain) {
        if (FirebaseAuth.getInstance().getCurrentUser() == null || domain == null || domain.isEmpty()) {
            return;
        }
        RetrofitClient.getApiService().removeSite(domain).enqueue(new Callback<java.util.Map<String, Object>>() {
            @Override
            public void onResponse(Call<java.util.Map<String, Object>> call, Response<java.util.Map<String, Object>> response) {
                if (!response.isSuccessful()) {
                    Log.w(TAG, "removeSite failed: " + response.code());
                }
            }

            @Override
            public void onFailure(Call<java.util.Map<String, Object>> call, Throwable t) {
                Log.w(TAG, "removeSite error", t);
            }
        });
    }

    public static String domainOf(String url) {
        if (url == null) return "";
        String cleaned = url.replace("https://", "").replace("http://", "");
        int slash = cleaned.indexOf('/');
        return (slash >= 0 ? cleaned.substring(0, slash) : cleaned).toLowerCase();
    }
}
