package com.inzira.app;

import android.app.Application;

public class InziraApp extends Application {

    @Override
    public void onCreate() {
        super.onCreate();
        RetrofitClient.init(this);
        PushRegistrar.registerIfLoggedIn();
    }
}
