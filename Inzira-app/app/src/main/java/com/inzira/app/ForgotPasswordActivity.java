package com.inzira.app;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.textfield.TextInputEditText;
import com.google.firebase.auth.FirebaseAuth;
import java.util.Locale;

public class ForgotPasswordActivity extends AppCompatActivity {

    private TextInputEditText etEmail;
    private ProgressBar progressBar;
    private Button btnSendCode;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_forgot_password);

        etEmail = findViewById(R.id.etEmail);
        btnSendCode = findViewById(R.id.btnSendCode);
        progressBar = findViewById(R.id.progressBar);
        TextView tvSignIn = findViewById(R.id.tvSignIn);

        findViewById(R.id.btnBack).setOnClickListener(v -> finish());
        tvSignIn.setOnClickListener(v -> finish());

        btnSendCode.setOnClickListener(v -> sendReset());
    }

    private void sendReset() {
        String email = etEmail.getText() != null
                ? etEmail.getText().toString().trim().toLowerCase(Locale.ROOT) : "";
        if (!FirebaseAuthHelper.isValidEmail(email)) {
            Toast.makeText(this, "Enter a valid email address", Toast.LENGTH_SHORT).show();
            return;
        }

        FirebaseAuth auth = FirebaseUtil.auth();
        if (FirebaseAuthHelper.isEnabled() && auth != null) {
            setLoading(true);
            auth.sendPasswordResetEmail(email)
                    .addOnSuccessListener(unused -> {
                        setLoading(false);
                        Toast.makeText(this,
                                "Password reset email sent. Check your inbox.",
                                Toast.LENGTH_LONG).show();
                        finish();
                    })
                    .addOnFailureListener(e -> {
                        setLoading(false);
                        Toast.makeText(this, FirebaseAuthHelper.resetErrorMessage(e),
                                Toast.LENGTH_LONG).show();
                    });
            return;
        }

        Toast.makeText(this,
                "Password reset requires Firebase. Enable google-services.json and Email auth in Firebase Console.",
                Toast.LENGTH_LONG).show();
    }

    private void setLoading(boolean loading) {
        if (progressBar != null) {
            progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        }
        btnSendCode.setEnabled(!loading);
    }
}
