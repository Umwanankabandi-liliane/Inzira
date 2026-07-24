package com.inzira.app;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import java.io.IOException;
import okhttp3.Interceptor;
import okhttp3.Request;
import okhttp3.Response;

public class AuthInterceptor implements Interceptor {

    @Override
    public Response intercept(Chain chain) throws IOException {
        Request request = chain.request();
        String path = request.url().encodedPath();
        if (!path.contains("/me/")) {
            return chain.proceed(request);
        }

        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) {
            return chain.proceed(request);
        }

        try {
            String token = com.google.android.gms.tasks.Tasks.await(user.getIdToken(false)).getToken();
            if (token != null && !token.isEmpty()) {
                request = request.newBuilder()
                        .header("Authorization", "Bearer " + token)
                        .build();
            }
        } catch (Exception ignored) {
            // proceed without auth header
        }
        return chain.proceed(request);
    }
}
