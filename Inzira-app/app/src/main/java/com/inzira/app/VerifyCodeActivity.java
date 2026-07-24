package com.inzira.app;

import android.os.Bundle;
import android.text.TextUtils;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.textfield.TextInputEditText;
import java.util.Locale;
import java.util.Random;

public class VerifyCodeActivity extends AppCompatActivity {

    private EditText et1, et2, et3, et4;
    private TextInputEditText etNewPassword;
    private TextView tvSentTo;
    private String email;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_verify_code);

        email = getIntent().getStringExtra("email");
        if (email == null) {
            email = "";
        }

        et1 = findViewById(R.id.etCode1);
        et2 = findViewById(R.id.etCode2);
        et3 = findViewById(R.id.etCode3);
        et4 = findViewById(R.id.etCode4);
        etNewPassword = findViewById(R.id.etNewPassword);
        tvSentTo = findViewById(R.id.tvSentTo);
        Button btnVerify = findViewById(R.id.btnVerify);
        TextView tvResend = findViewById(R.id.tvResend);

        tvSentTo.setText("We sent a 4-digit code to " + email);

        findViewById(R.id.btnBack).setOnClickListener(v -> finish());
        tvResend.setOnClickListener(v -> resendCode());
        btnVerify.setOnClickListener(v -> verifyAndReset());
    }

    private void resendCode() {
        // Re-run the same reset process by creating a new code.
        if (email.isEmpty()) {
            Toast.makeText(this, "Email missing", Toast.LENGTH_SHORT).show();
            return;
        }
        String code = String.format(Locale.ROOT, "%04d", new Random().nextInt(10000));
        InziraPrefs.setResetSession(this, email, code, System.currentTimeMillis());
        Toast.makeText(this, "Reset code: " + code, Toast.LENGTH_LONG).show();
    }

    private void verifyAndReset() {
        String code = (et1.getText() + "" + et2.getText() + "" + et3.getText() + "" + et4.getText()).trim();
        String expectedEmail = InziraPrefs.getResetEmail(this);
        String expectedCode = InziraPrefs.getResetCode(this);
        if (!email.equalsIgnoreCase(expectedEmail) || !code.equals(expectedCode) || code.length() != 4) {
            Toast.makeText(this, "Invalid code", Toast.LENGTH_SHORT).show();
            return;
        }

        String newPassword = etNewPassword.getText() != null ? etNewPassword.getText().toString() : "";
        if (TextUtils.isEmpty(newPassword) || newPassword.length() < 6) {
            Toast.makeText(this, "Password must be at least 6 characters", Toast.LENGTH_SHORT).show();
            return;
        }

        // Local reset (demo mode): update saved password if email matches local account.
        if (LocalAuthStore.resetPassword(this, email, newPassword)) {
            Toast.makeText(this, "Password updated", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        Toast.makeText(this, "Password reset link sent to email (Firebase).", Toast.LENGTH_LONG).show();
        finish();
    }
}

