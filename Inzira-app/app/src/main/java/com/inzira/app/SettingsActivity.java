package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.FirebaseDatabase;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class SettingsActivity extends AppCompatActivity {

    private TextView tvInitials;
    private TextView tvName;
    private TextView tvEmail;
    private TextView tvBackendUrl;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!SessionManager.isLoggedIn(this)) {
            NavHelper.openLogin(this, false, false);
            finish();
            return;
        }

        setContentView(R.layout.activity_settings);

        tvInitials = findViewById(R.id.tvInitials);
        tvName = findViewById(R.id.tvName);
        tvEmail = findViewById(R.id.tvEmail);
        tvBackendUrl = findViewById(R.id.tvBackendUrl);
        LinearLayout rowSignOut = findViewById(R.id.rowSignOut);
        LinearLayout rowInstitution = findViewById(R.id.rowInstitution);
        LinearLayout rowBackend = findViewById(R.id.rowBackend);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        loadProfile();
        applyLanguageUi();
        refreshBackendLabel();

        rowSignOut.setOnClickListener(v -> signOut());
        rowInstitution.setOnClickListener(v ->
                startActivity(new Intent(SettingsActivity.this, MifotraPinActivity.class)));
        rowBackend.setOnClickListener(v -> showBackendDialog());

        NavHelper.wireBottomNav(this, bottomNav, R.id.navSettings);
    }

    private void applyLanguageUi() {
        boolean rw = InziraPrefs.isKinyarwanda(this);
        ((TextView) findViewById(R.id.tvSettingsTitle)).setText(rw ? "Igenamiterere" : "Settings");
        ((TextView) findViewById(R.id.tvSignOutLabel)).setText(LanguageHelper.signOutButton(this));
        ((TextView) findViewById(R.id.tvBackendTitle)).setText(rw ? "Seriveri ya Inzira" : "Server connection");
        ((TextView) findViewById(R.id.tvMifotraTitle)).setText(rw
                ? "MIFOTRA staff portal" : "MIFOTRA staff portal");
        ((TextView) findViewById(R.id.tvMifotraSub)).setText(rw
                ? "Dashboard y'ubuyobozi — analytics n'imbuga zemewe"
                : "Ministry dashboard — analytics & verified websites");
    }

    private void refreshBackendLabel() {
        tvBackendUrl.setText(BackendConfig.displayUrl(this));
    }

    private void showBackendDialog() {
        boolean rw = InziraPrefs.isKinyarwanda(this);
        EditText input = new EditText(this);
        input.setText(BackendConfig.displayUrl(this));
        input.setHint("https://your-server.onrender.com");
        input.setPadding(48, 32, 48, 32);
        input.setSingleLine(true);

        new AlertDialog.Builder(this)
                .setTitle(rw ? "Seriveri ya Inzira" : "Inzira server URL")
                .setMessage(rw
                        ? "Shyiramo URL y'inyubako y'Inzira (HTTPS mu bucukumbuzi)."
                        : "Enter your deployed Inzira backend URL (HTTPS in production).")
                .setView(input)
                .setPositiveButton(rw ? "Bika" : "Save", (d, w) -> {
                    BackendConfig.setBaseUrl(this, input.getText().toString());
                    refreshBackendLabel();
                    testBackendConnection();
                })
                .setNeutralButton(rw ? "Default" : "Reset", (d, w) -> {
                    BackendConfig.resetToDefault(this);
                    refreshBackendLabel();
                    Toast.makeText(this, rw ? "Byasubijwe" : "Reset to default", Toast.LENGTH_SHORT).show();
                })
                .setNegativeButton(rw ? "Hagarika" : "Cancel", null)
                .show();
    }

    private void testBackendConnection() {
        boolean rw = InziraPrefs.isKinyarwanda(this);
        RetrofitClient.getApiService().health().enqueue(new Callback<HealthResponse>() {
            @Override
            public void onResponse(Call<HealthResponse> call, Response<HealthResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    Toast.makeText(SettingsActivity.this,
                            rw ? "Seriveri ikora" : "Server connected",
                            Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(SettingsActivity.this,
                            rw ? "Seriveri ntiyitabira" : "Server unreachable",
                            Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onFailure(Call<HealthResponse> call, Throwable t) {
                Toast.makeText(SettingsActivity.this,
                        rw ? "Ntibyashoboye guhuza" : "Connection failed: " + t.getMessage(),
                        Toast.LENGTH_LONG).show();
            }
        });
    }

    private void loadProfile() {
        String email = SessionManager.getEmail(this);
        tvEmail.setText(email != null && !email.isEmpty() ? email : "Signed in");

        if (SessionManager.usesFirebase()) {
            FirebaseUser user = FirebaseUtil.currentUser();
            if (user != null) {
                FirebaseDatabase.getInstance().getReference("users")
                        .child(user.getUid())
                        .get()
                        .addOnSuccessListener(snapshot -> {
                            String name = snapshot.child("name").getValue(String.class);
                            if (name == null || name.trim().isEmpty()) {
                                name = user.getDisplayName() != null ? user.getDisplayName() : "User";
                            }
                            tvName.setText(name);
                            tvInitials.setText(getInitials(name));
                        });
            }
            return;
        }

        String name = LocalAuthStore.getName(this);
        tvName.setText(name != null && !name.isEmpty() ? name : "User");
        tvInitials.setText(getInitials(name != null ? name : "User"));
    }

    private void signOut() {
        SessionManager.signOut(this);
        Toast.makeText(this,
                InziraPrefs.isKinyarwanda(this) ? "Wasohotse" : "Signed out",
                Toast.LENGTH_SHORT).show();
        NavHelper.openLogin(this, true, false);
    }

    private String getInitials(String name) {
        String[] parts = name.trim().split("\\s+");
        if (parts.length >= 2) {
            return ("" + parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
        }
        if (!name.isEmpty()) {
            return name.substring(0, 1).toUpperCase();
        }
        return "?";
    }
}
