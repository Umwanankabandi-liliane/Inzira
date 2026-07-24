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

public class MainActivity extends AppCompatActivity {

    private TextView btnEnglish;
    private TextView btnKinyarwanda;
    private TextView tvHeaderSubtitle;
    private TextView tvEmailLabel;
    private TextView tvPasswordLabel;
    private TextInputEditText etEmail;
    private TextInputEditText etPassword;
    private TextView tvAuthError;
    private TextView tvForgotPassword;
    private TextView tvOr;
    private TextView tvCreateAccountLink;
    private Button btnSignIn;
    private Button btnGoogle;
    private ProgressBar progressAuth;
    private FirebaseAuth auth;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (SessionManager.isLoggedIn(this)) {
            NavHelper.openAppHome(this);
            finish();
            return;
        }

        setContentView(R.layout.activity_main);
        auth = FirebaseUtil.auth();

        View languageFooter = findViewById(R.id.languageFooter);
        if (languageFooter != null) {
            languageFooter.setVisibility(View.GONE);
        }

        btnEnglish = findViewById(R.id.btnEnglish);
        btnKinyarwanda = findViewById(R.id.btnKinyarwanda);
        etEmail = findViewById(R.id.etEmail);
        etPassword = findViewById(R.id.etPassword);
        tvAuthError = findViewById(R.id.tvAuthError);
        tvForgotPassword = findViewById(R.id.tvForgotPassword);
        tvOr = findViewById(R.id.tvOr);
        btnSignIn = findViewById(R.id.btnSignIn);
        btnGoogle = findViewById(R.id.btnGoogle);
        progressAuth = findViewById(R.id.progressAuth);
        tvCreateAccountLink = findViewById(R.id.tvCreateAccountLink);
        tvHeaderSubtitle = findViewById(R.id.tvHeaderSubtitle);
        tvEmailLabel = findViewById(R.id.tvEmailLabel);
        tvPasswordLabel = findViewById(R.id.tvPasswordLabel);

        if (InziraPrefs.isKinyarwanda(this)) {
            selectKinyarwanda();
        } else {
            selectEnglish();
        }

        if (btnEnglish != null) {
            btnEnglish.setOnClickListener(v -> selectEnglish());
        }
        if (btnKinyarwanda != null) {
            btnKinyarwanda.setOnClickListener(v -> selectKinyarwanda());
        }
        btnSignIn.setOnClickListener(v -> attemptLogin());
        tvCreateAccountLink.setOnClickListener(v -> openRegister());
        tvForgotPassword.setOnClickListener(v ->
                startActivity(new Intent(MainActivity.this, ForgotPasswordActivity.class)));
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
        if (btnEnglish != null && btnKinyarwanda != null) {
            LanguageHelper.applyLanguageChipStyle(this, btnEnglish, btnKinyarwanda);
        }
    }

    private void attemptLogin() {
        String email = etEmail.getText() != null ? etEmail.getText().toString().trim() : "";
        String password = etPassword.getText() != null ? etPassword.getText().toString() : "";

        tvAuthError.setVisibility(View.GONE);

        LoginHelper.attemptLogin(this, auth, email, password, new LoginHelper.Callback() {
            @Override
            public void onSuccess() {
                NavHelper.openAppHome(MainActivity.this);
                finish();
            }

            @Override
            public void onError(String message) {
                tvAuthError.setText(message);
                tvAuthError.setVisibility(View.VISIBLE);
            }

            @Override
            public void onLoading(boolean loading) {
                progressAuth.setVisibility(loading ? View.VISIBLE : View.GONE);
                btnSignIn.setEnabled(!loading);
                btnGoogle.setEnabled(!loading);
            }
        });
    }

    private void selectEnglish() {
        InziraPrefs.setLanguage(this, InziraPrefs.ENGLISH);
        LanguageHelper.applyLanguageChipStyle(this, btnEnglish, btnKinyarwanda);
        applyLanguageUi();
    }

    private void selectKinyarwanda() {
        InziraPrefs.setLanguage(this, InziraPrefs.KINYARWANDA);
        LanguageHelper.applyLanguageChipStyle(this, btnEnglish, btnKinyarwanda);
        applyLanguageUi();
    }

    private void applyLanguageUi() {
        LanguageHelper.applyWelcomeScreen(this, tvHeaderSubtitle, tvEmailLabel, tvPasswordLabel,
                btnSignIn, etEmail, btnGoogle, tvForgotPassword, tvOr,
                findViewById(R.id.tvNewHerePrompt), tvCreateAccountLink);
    }

    private void openRegister() {
        startActivity(new Intent(MainActivity.this, RegisterActivity.class));
    }
}
