package com.inzira.app;

import android.content.Context;
import com.google.firebase.auth.FirebaseAuth;

public final class LoginHelper {

    public interface Callback {
        void onSuccess();

        void onError(String message);

        void onLoading(boolean loading);
    }

    private LoginHelper() {
    }

    public static void attemptLogin(Context context, FirebaseAuth auth, String email, String password,
                                    Callback callback) {
        if (!FirebaseAuthHelper.isValidEmail(email)) {
            callback.onError("Please enter a valid email address");
            return;
        }
        if (password.isEmpty()) {
            callback.onError("Please enter your password");
            return;
        }
        if (password.length() < 6) {
            callback.onError("Password must be at least 6 characters");
            return;
        }

        callback.onLoading(true);

        if (FirebaseAuthHelper.isEnabled() && auth != null) {
            auth.signInWithEmailAndPassword(email.trim(), password)
                    .addOnSuccessListener(result -> {
                        callback.onLoading(false);
                        LocalAuthStore.clearAccount(context);
                        SessionManager.syncFirebaseProfile(context);
                        PushRegistrar.registerIfLoggedIn();
                        callback.onSuccess();
                    })
                    .addOnFailureListener(e -> {
                        callback.onLoading(false);
                        callback.onError(FirebaseAuthHelper.loginErrorMessage(e));
                    });
            return;
        }

        callback.onLoading(false);
        if (BuildConfig.DEBUG && LocalAuthStore.login(context, email, password)) {
            callback.onSuccess();
        } else if (!FirebaseAuthHelper.isEnabled()) {
            callback.onError("Sign-in requires Firebase. Add google-services.json to the app.");
        } else if (!LocalAuthStore.hasAccount(context)) {
            callback.onError("No account yet — tap Create account below. "
                    + "(Firebase is required for production sign-in.)");
        } else {
            callback.onError("Wrong email or password.");
        }
    }
}
