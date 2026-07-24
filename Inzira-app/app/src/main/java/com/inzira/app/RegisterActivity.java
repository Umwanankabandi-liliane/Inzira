package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.textfield.TextInputEditText;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.FirebaseDatabase;
import java.util.HashMap;
import java.util.Map;

public class RegisterActivity extends AppCompatActivity {

    private EditText etName;
    private EditText etEmail;
    private TextInputEditText etPassword;
    private Spinner spDistrict;
    private Spinner spAge;
    private CheckBox cbTerms;
    private Button btnRegister;
    private TextView tvLogin;
    private ProgressBar progressBar;
    private FirebaseAuth auth;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (SessionManager.isLoggedIn(this)) {
            NavHelper.openAppHome(this);
            finish();
            return;
        }

        setContentView(R.layout.activity_register);

        auth = FirebaseUtil.auth();

        etName = findViewById(R.id.etName);
        etEmail = findViewById(R.id.etEmail);
        etPassword = findViewById(R.id.etPassword);
        spDistrict = findViewById(R.id.spDistrict);
        spAge = findViewById(R.id.spAge);
        cbTerms = findViewById(R.id.cbTerms);
        btnRegister = findViewById(R.id.btnRegister);
        tvLogin = findViewById(R.id.tvLogin);
        progressBar = findViewById(R.id.progressBar);

        DistrictHelper.setupSpinner(this, spDistrict);
        AgeHelper.setupSpinner(this, spAge);
        applyLanguageUi();

        btnRegister.setOnClickListener(v -> attemptRegister());
        tvLogin.setOnClickListener(v -> {
            startActivity(new Intent(RegisterActivity.this, MainActivity.class));
            finish();
        });
        findViewById(R.id.btnBack).setOnClickListener(v -> finish());
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyLanguageUi();
    }

    private void applyLanguageUi() {
        LanguageHelper.applyRegisterScreen(this,
                findViewById(R.id.tvRegisterTitle),
                findViewById(R.id.tvRegisterSubtitle),
                findViewById(R.id.tvNameLabel),
                findViewById(R.id.tvDistrictLabel),
                findViewById(R.id.tvAgeLabel),
                findViewById(R.id.tvEmailLabel),
                findViewById(R.id.tvPasswordLabel),
                etName,
                etEmail,
                findViewById(R.id.tvTerms),
                btnRegister,
                findViewById(R.id.tvAlreadyRegistered),
                tvLogin);
    }

    private void attemptRegister() {
        String name = etName.getText().toString().trim();
        String email = etEmail.getText().toString().trim();
        String password = etPassword.getText() != null ? etPassword.getText().toString() : "";

        if (name.isEmpty() || email.isEmpty() || password.isEmpty()) {
            Toast.makeText(this, "Please fill all fields", Toast.LENGTH_SHORT).show();
            return;
        }
        if (!FirebaseAuthHelper.isValidEmail(email)) {
            Toast.makeText(this, "Please enter a valid email address", Toast.LENGTH_SHORT).show();
            return;
        }
        if (password.length() < 6) {
            Toast.makeText(this, "Password must be at least 6 characters", Toast.LENGTH_SHORT).show();
            return;
        }
        if (!cbTerms.isChecked()) {
            Toast.makeText(this, "Please accept the terms of service", Toast.LENGTH_SHORT).show();
            return;
        }

        String district = DistrictHelper.selectedDistrict(spDistrict);
        String age = AgeHelper.selectedAge(spAge);

        if (FirebaseAuthHelper.isEnabled() && auth != null) {
            setLoading(true);
            auth.createUserWithEmailAndPassword(email.trim(), password)
                    .addOnSuccessListener(result ->
                            saveFirebaseProfile(result.getUser(), name, email, district, age))
                    .addOnFailureListener(e -> {
                        setLoading(false);
                        Toast.makeText(this, FirebaseAuthHelper.registerErrorMessage(e),
                                Toast.LENGTH_LONG).show();
                    });
            return;
        }

        if (!FirebaseAuthHelper.isEnabled()) {
            if (BuildConfig.DEBUG) {
                Toast.makeText(this,
                        "Firebase not configured — debug offline account on this device only.",
                        Toast.LENGTH_LONG).show();
                registerLocally(name, email, password, district, age);
            } else {
                Toast.makeText(this,
                        "Registration requires Firebase. Add google-services.json to the app.",
                        Toast.LENGTH_LONG).show();
            }
            return;
        }
    }

    private void saveFirebaseProfile(FirebaseUser user, String name, String email, String district, String age) {
        if (user == null) {
            setLoading(false);
            Toast.makeText(this, "Registration failed", Toast.LENGTH_SHORT).show();
            return;
        }

        LocalAuthStore.clearAccount(this);

        String language = InziraPrefs.getLanguage(this);
        Map<String, Object> profile = new HashMap<>();
        profile.put("name", name);
        profile.put("email", email);
        profile.put("language", language);
        if (district != null && !district.isEmpty()) {
            profile.put("district", district);
            InziraPrefs.setDistrict(RegisterActivity.this, district);
        }
        if (age != null && !age.isEmpty()) {
            profile.put("age", age);
            InziraPrefs.setAge(RegisterActivity.this, age);
        }

        FirebaseDatabase.getInstance().getReference("users")
                .child(user.getUid())
                .setValue(profile)
                .addOnCompleteListener(task -> {
                    setLoading(false);
                    goToHome();
                });
    }

    private void registerLocally(String name, String email, String password, String district, String age) {
        setLoading(false);
        LocalAuthStore.register(this, name, email, password, district);
        InziraPrefs.setAge(this, age);
        Toast.makeText(this, "Account created — welcome to Inzira!", Toast.LENGTH_SHORT).show();
        goToHome();
    }

    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        btnRegister.setEnabled(!loading);
    }

    private void goToHome() {
        NavHelper.openAppHome(this);
        finish();
    }
}
