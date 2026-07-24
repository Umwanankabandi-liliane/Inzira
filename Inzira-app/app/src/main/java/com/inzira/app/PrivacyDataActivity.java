package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.Switch;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.FirebaseDatabase;

public class PrivacyDataActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_privacy_data);

        Switch switchShareAnon = findViewById(R.id.switchShareAnon);
        Switch switchPersonalized = findViewById(R.id.switchPersonalized);
        Switch switchAnalytics = findViewById(R.id.switchAnalytics);
        Button btnDeleteData = findViewById(R.id.btnDeleteData);

        findViewById(R.id.btnBack).setOnClickListener(v -> finish());

        switchShareAnon.setChecked(InziraPrefs.getShareAnonymizedSearch(this));
        switchPersonalized.setChecked(InziraPrefs.getPersonalizedNotifications(this));
        switchAnalytics.setChecked(InziraPrefs.getUsageAnalytics(this));

        switchShareAnon.setOnCheckedChangeListener((buttonView, isChecked) ->
                InziraPrefs.setShareAnonymizedSearch(this, isChecked));
        switchPersonalized.setOnCheckedChangeListener((buttonView, isChecked) ->
                InziraPrefs.setPersonalizedNotifications(this, isChecked));
        switchAnalytics.setOnCheckedChangeListener((buttonView, isChecked) ->
                InziraPrefs.setUsageAnalytics(this, isChecked));

        btnDeleteData.setOnClickListener(v -> confirmDelete());
    }

    private void confirmDelete() {
        if (!SessionManager.isLoggedIn(this)) {
            Toast.makeText(this, "Not signed in", Toast.LENGTH_SHORT).show();
            return;
        }

        new AlertDialog.Builder(this)
                .setTitle("Delete account and data")
                .setMessage("This will permanently delete your account and followed websites.")
                .setPositiveButton("Delete", (dialog, which) -> deleteNow())
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void deleteNow() {
        FirebaseAuth auth = FirebaseUtil.auth();
        if (auth == null) {
            auth = FirebaseAuth.getInstance();
        }
        FirebaseUser user = auth.getCurrentUser();

        if (user != null) {
            String uid = user.getUid();
            FirebaseDatabase.getInstance().getReference("users").child(uid).removeValue();
            FirebaseDatabase.getInstance().getReference("followed_sites").child(uid).removeValue();
            user.delete()
                    .addOnSuccessListener(unused -> {
                        LocalAuthStore.clearAccount(this);
                        SessionManager.signOut(this);
                        goToHome();
                    })
                    .addOnFailureListener(e ->
                            Toast.makeText(this, "Delete failed: " + e.getMessage(), Toast.LENGTH_LONG).show());
            return;
        }

        LocalAuthStore.clearAccount(this);
        SessionManager.signOut(this);
        goToHome();
    }

    private void goToHome() {
        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}

