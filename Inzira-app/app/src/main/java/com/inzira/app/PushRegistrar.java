package com.inzira.app;

import android.util.Log;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.messaging.FirebaseMessaging;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public final class PushRegistrar {

    private static final String TAG = "PushRegistrar";

    private PushRegistrar() {
    }

    public static void registerIfLoggedIn() {
        if (FirebaseAuth.getInstance().getCurrentUser() == null) {
            return;
        }
        FirebaseMessaging.getInstance().getToken()
                .addOnSuccessListener(PushRegistrar::sendTokenToBackend)
                .addOnFailureListener(e -> Log.w(TAG, "FCM token fetch failed", e));
    }

    public static void sendTokenToBackend(String token) {
        if (token == null || token.isEmpty() || FirebaseAuth.getInstance().getCurrentUser() == null) {
            return;
        }
        RetrofitClient.getApiService().registerFcm(new FcmTokenBody(token))
                .enqueue(new Callback<java.util.Map<String, Object>>() {
                    @Override
                    public void onResponse(Call<java.util.Map<String, Object>> call,
                                           Response<java.util.Map<String, Object>> response) {
                        if (response.isSuccessful()) {
                            Log.d(TAG, "FCM token registered with backend");
                        } else {
                            Log.w(TAG, "FCM register failed: " + response.code());
                        }
                    }

                    @Override
                    public void onFailure(Call<java.util.Map<String, Object>> call, Throwable t) {
                        Log.w(TAG, "FCM register error", t);
                    }
                });
    }
}
