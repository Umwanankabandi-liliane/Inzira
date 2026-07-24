package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class LanguageActivity extends AppCompatActivity {

    private TextView btnEnglish;
    private TextView btnKinyarwanda;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (SessionManager.isLoggedIn(this)) {
            NavHelper.openAppHome(this);
            finish();
            return;
        }

        if (InziraPrefs.hasChosenLanguage(this)) {
            startActivity(new Intent(this, MainActivity.class));
            finish();
            return;
        }

        setContentView(R.layout.activity_language);

        btnEnglish = findViewById(R.id.btnEnglish);
        btnKinyarwanda = findViewById(R.id.btnKinyarwanda);
        Button btnContinue = findViewById(R.id.btnContinue);

        if (InziraPrefs.isKinyarwanda(this)) {
            selectKinyarwanda();
        } else {
            selectEnglish();
        }

        btnEnglish.setOnClickListener(v -> selectEnglish());
        btnKinyarwanda.setOnClickListener(v -> selectKinyarwanda());
        btnContinue.setOnClickListener(v -> {
            InziraPrefs.setLanguageChosen(this, true);
            startActivity(new Intent(this, RegisterActivity.class));
            finish();
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (findViewById(R.id.tvChooseLanguage) != null) {
            applyLanguageUi();
        }
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
        TextView tvSubtitle = findViewById(R.id.tvLanguageSubtitle);
        TextView tvChoose = findViewById(R.id.tvChooseLanguage);
        TextView tvHint = findViewById(R.id.tvLanguageHint);
        TextView tvTagline = findViewById(R.id.tvTagline);
        Button btnContinue = findViewById(R.id.btnContinue);

        if (tvSubtitle != null) {
            tvSubtitle.setText(LanguageHelper.welcomeSubtitle(this));
        }
        if (tvChoose != null) {
            tvChoose.setText(LanguageHelper.chooseLanguageLabel(this));
        }
        if (tvHint != null) {
            tvHint.setText(InziraPrefs.isKinyarwanda(this)
                    ? "Select English or Kinyarwanda"
                    : "Hitamo Icyongereza cyangwa Ikinyarwanda");
        }
        if (tvTagline != null) {
            tvTagline.setText(LanguageHelper.welcomeTagline(this));
        }
        if (btnContinue != null) {
            btnContinue.setText(LanguageHelper.continueLabel(this));
        }
    }
}
