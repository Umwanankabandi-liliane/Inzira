package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.textfield.TextInputEditText;
import com.google.firebase.auth.FirebaseAuth;

public class LoginActivity extends AppCompatActivity {

    private TextInputEditText etEmail;
    private TextInputEditText etPassword;
    private TextView tvEmailLabel;
    private TextView tvPasswordLabel;
    private TextView tvHeaderSubtitle;
    private TextView tvForgotPassword;
    private TextView tvOr;
    private Button btnLogin;
    private Button btnGoogle;
    private TextView tvRegister;
    private TextView tvError;
    private ProgressBar progressBar;
    private FirebaseAuth auth;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        auth = FirebaseUtil.auth();

        etEmail = findViewById(R.id.etEmail);
        etPassword = findViewById(R.id.etPassword);
        tvEmailLabel = findViewById(R.id.tvEmailLabel);
        tvPasswordLabel = findViewById(R.id.tvPasswordLabel);
        tvHeaderSubtitle = findViewById(R.id.tvHeaderSubtitle);
        tvForgotPassword = findViewById(R.id.tvForgotPassword);
        tvOr = findViewById(R.id.tvOr);
        btnLogin = findViewById(R.id.btnLogin);
        btnGoogle = findViewById(R.id.btnGoogle);
        tvRegister = findViewById(R.id.tvRegister);
        tvError = findViewById(R.id.tvError);
        progressBar = findViewById(R.id.progressBar);

        applyLanguageUi();

        btnLogin.setOnClickListener(v -> attemptLogin());
        tvRegister.setOnClickListener(v -> {
            startActivity(new Intent(LoginActivity.this, RegisterActivity.class));
            finish();
        });
        findViewById(R.id.btnBack).setOnClickListener(v -> finish());
        tvForgotPassword.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, ForgotPasswordActivity.class)));
        btnGoogle.setOnClickListener(v ->
                Toast.makeText(this, LanguageHelper.googleSignInHint(this), Toast.LENGTH_SHORT).show());

        etPassword.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_DONE) {
                attemptLogin();
                return true;
            }
            return false;
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyLanguageUi();
    }

    private void applyLanguageUi() {
        LanguageHelper.applyWelcomeScreen(this, tvHeaderSubtitle, tvEmailLabel, tvPasswordLabel,
                btnLogin, etEmail, btnGoogle, tvForgotPassword, tvOr,
                findViewById(R.id.tvNewHerePrompt), tvRegister);
    }

    private void attemptLogin() {
        String email = etEmail.getText() != null ? etEmail.getText().toString().trim() : "";
        String password = etPassword.getText() != null ? etPassword.getText().toString() : "";

        tvError.setVisibility(View.GONE);

        LoginHelper.attemptLogin(this, auth, email, password, new LoginHelper.Callback() {
            @Override
            public void onSuccess() {
                NavHelper.openAppHome(LoginActivity.this);
                finish();
            }

            @Override
            public void onError(String message) {
                showError(message);
            }

            @Override
            public void onLoading(boolean loading) {
                setLoading(loading);
            }
        });
    }

    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        btnLogin.setEnabled(!loading);
    }

    private void showError(String message) {
        tvError.setText(message);
        tvError.setVisibility(View.VISIBLE);
    }
}
