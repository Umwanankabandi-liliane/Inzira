package com.inzira.app;

import android.content.Context;
import android.content.Intent;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.bottomnavigation.BottomNavigationView;

public final class NavHelper {

    private NavHelper() {
    }

    /** After successful sign-in or register. */
    public static void openAppHome(Context context) {
        Intent intent = new Intent(context, DashboardActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        context.startActivity(intent);
    }

    /** Back to sign-in (optionally signs out). */
    public static void openLogin(Context context, boolean finishCurrent, boolean signOut) {
        if (signOut) {
            SessionManager.signOut(context);
        }
        Intent intent;
        if (InziraPrefs.hasChosenLanguage(context)) {
            intent = new Intent(context, MainActivity.class);
        } else {
            intent = new Intent(context, LanguageActivity.class);
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        context.startActivity(intent);
        if (finishCurrent && context instanceof AppCompatActivity) {
            ((AppCompatActivity) context).finish();
        }
    }

    /** Shared bottom navigation handler for main app screens. */
    public static boolean onBottomNavSelected(AppCompatActivity activity, int itemId) {
        if (itemId == R.id.navDashboard) {
            if (!(activity instanceof DashboardActivity)) {
                activity.startActivity(new Intent(activity, DashboardActivity.class));
                activity.finish();
            }
            return true;
        } else if (itemId == R.id.navMatches) {
            if (!(activity instanceof MatchesActivity)) {
                activity.startActivity(new Intent(activity, MatchesActivity.class));
                activity.finish();
            }
            return true;
        } else if (itemId == R.id.navAssistant) {
            if (!(activity instanceof AssistantActivity)) {
                activity.startActivity(new Intent(activity, AssistantActivity.class));
                activity.finish();
            }
            return true;
        } else if (itemId == R.id.navSettings) {
            if (!(activity instanceof SettingsActivity)) {
                activity.startActivity(new Intent(activity, SettingsActivity.class));
                activity.finish();
            }
            return true;
        }
        return false;
    }

    public static void wireBottomNav(AppCompatActivity activity, BottomNavigationView bottomNav, int selectedId) {
        localizeBottomNav(activity, bottomNav);
        bottomNav.setSelectedItemId(selectedId);
        bottomNav.setOnItemSelectedListener(item ->
                onBottomNavSelected(activity, item.getItemId()));
    }

    public static void localizeBottomNav(Context context, BottomNavigationView bottomNav) {
        boolean rw = InziraPrefs.isKinyarwanda(context);
        android.view.Menu menu = bottomNav.getMenu();
        menu.findItem(R.id.navDashboard).setTitle(rw ? "Ikarita" : "Map");
        menu.findItem(R.id.navMatches).setTitle(rw ? "Amahirwe yanjye" : "My matches");
        menu.findItem(R.id.navAssistant).setTitle(rw ? "Umuyobozi" : "Assistant");
        menu.findItem(R.id.navSettings).setTitle(rw ? "Igenamiterere" : "Settings");
    }
}
