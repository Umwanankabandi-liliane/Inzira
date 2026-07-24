package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * MIFOTRA staff portal — separate from youth accounts.
 * Does NOT sign in to Firebase; youth stay logged in with their own account.
 */
public class MifotraPinActivity extends AppCompatActivity {

    private EditText etStaffEmail;
    private EditText etStaffPassword;
    private TextView tvError;
    private ProgressBar progressBar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (InziraPrefs.isMifotraSessionValid(this)) {
            openDashboard();
            return;
        }

        setContentView(R.layout.activity_mifotra_pin);

        etStaffEmail = findViewById(R.id.etStaffEmail);
        etStaffPassword = findViewById(R.id.etStaffPassword);
        tvError = findViewById(R.id.tvPinError);
        progressBar = findViewById(R.id.progressBar);
        Button btnSignIn = findViewById(R.id.btnUnlock);
        ImageButton btnBack = findViewById(R.id.btnBack);
        TextView tvHint = findViewById(R.id.tvStaffHint);

        tvHint.setText("Ministry staff only. Use your work email "
                + StaffEmailHelper.requiredDomainHint()
                + " and the password from MIFOTRA IT.\n\n"
                + "Youth accounts are separate — register from the home screen with your personal email.");

        btnBack.setOnClickListener(v -> finish());
        btnSignIn.setOnClickListener(v -> attemptStaffSignIn());

        etStaffPassword.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_DONE) {
                attemptStaffSignIn();
                return true;
            }
            return false;
        });

        loadStaffConfig();
    }

    private void loadStaffConfig() {
        RetrofitClient.getApiService().mifotraStaffConfig().enqueue(new Callback<MifotraStaffConfigResponse>() {
            @Override
            public void onResponse(Call<MifotraStaffConfigResponse> call, Response<MifotraStaffConfigResponse> response) {
                if (response.isSuccessful() && response.body() != null && !response.body().email_required) {
                    InziraPrefs.setMifotraSession(MifotraPinActivity.this, "dev-open",
                            System.currentTimeMillis() + 86400000L);
                    openDashboard();
                }
            }

            @Override
            public void onFailure(Call<MifotraStaffConfigResponse> call, Throwable t) {
                // Keep login screen
            }
        });
    }

    private void attemptStaffSignIn() {
        String email = etStaffEmail.getText().toString().trim().toLowerCase();
        String password = etStaffPassword.getText().toString();

        if (email.isEmpty() || password.isEmpty()) {
            showError("Enter work email and institution password");
            return;
        }
        if (!StaffEmailHelper.isStaffEmail(email)) {
            showError("Use your official MIFOTRA email " + StaffEmailHelper.requiredDomainHint());
            return;
        }

        tvError.setVisibility(View.GONE);
        setLoading(true);

        RetrofitClient.getApiService().verifyMifotraStaff(new MifotraStaffRequest(email, password))
                .enqueue(new Callback<MifotraPinResponse>() {
                    @Override
                    public void onResponse(Call<MifotraPinResponse> call, Response<MifotraPinResponse> response) {
                        setLoading(false);
                        if (response.isSuccessful() && response.body() != null && response.body().ok) {
                            MifotraPinResponse body = response.body();
                            long expiryMs = System.currentTimeMillis() + (body.expires_in * 1000L);
                            InziraPrefs.setMifotraSession(MifotraPinActivity.this, body.token, expiryMs);
                            openDashboard();
                            return;
                        }
                        showError("Invalid staff email or password. Contact MIFOTRA IT.");
                    }

                    @Override
                    public void onFailure(Call<MifotraPinResponse> call, Throwable t) {
                        setLoading(false);
                        Toast.makeText(MifotraPinActivity.this,
                                LanguageHelper.backendOfflineMessage(MifotraPinActivity.this),
                                Toast.LENGTH_LONG).show();
                    }
                });
    }

    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        findViewById(R.id.btnUnlock).setEnabled(!loading);
    }

    private void showError(String message) {
        tvError.setText(message);
        tvError.setVisibility(View.VISIBLE);
    }

    private void openDashboard() {
        startActivity(new Intent(this, MifotraDashboardActivity.class));
        finish();
    }
}
