package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.bottomnavigation.BottomNavigationView;

public class SearchActivity extends AppCompatActivity {

    private EditText etSearch;
    private ImageButton btnSearch;
    private BottomNavigationView bottomNav;
    private TextView tvHelloLabel;
    private TextView tvHelloName;
    private TextView tvVerifiedSubtitle;
    private boolean backendChecked = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!SessionManager.isLoggedIn(this)) {
            startActivity(new Intent(this, MainActivity.class));
            finish();
            return;
        }

        setContentView(R.layout.activity_search);

        etSearch  = findViewById(R.id.etSearch);
        btnSearch = findViewById(R.id.btnSearch);
        bottomNav = findViewById(R.id.bottomNav);
        tvHelloLabel = findViewById(R.id.tvHelloLabel);
        tvHelloName = findViewById(R.id.tvHelloName);
        tvVerifiedSubtitle = findViewById(R.id.tvVerifiedSubtitle);

        applyLanguageUi();

        findViewById(R.id.btnBackToLogin).setOnClickListener(v ->
                NavHelper.openLogin(SearchActivity.this, true, true));
        findViewById(R.id.btnProfile).setOnClickListener(v ->
                startActivity(new Intent(SearchActivity.this, SettingsActivity.class)));
        bottomNav.setSelectedItemId(R.id.navDashboard);
        NavHelper.wireBottomNav(this, bottomNav, R.id.navDashboard);
        checkBackendConnection();

        btnSearch.setOnClickListener(v -> submitSearch());

        etSearch.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                submitSearch();
                return true;
            }
            return false;
        });

        findViewById(R.id.chipAll).setOnClickListener(v -> openResults("opportunities", null));
        findViewById(R.id.chipJobs).setOnClickListener(v -> openResults("jobs", "job"));
        findViewById(R.id.chipScholarships).setOnClickListener(v -> openResults("scholarships", "scholarship"));
        findViewById(R.id.chipInternships).setOnClickListener(v -> openResults("internships", "internship"));
        findViewById(R.id.chipTraining).setOnClickListener(v -> openResults("training programs", "training"));
        findViewById(R.id.chipPrograms).setOnClickListener(v -> openResults("programs", "program"));
        findViewById(R.id.chipCompetitions).setOnClickListener(v -> openResults("competitions", "competition"));
        findViewById(R.id.chipCourses).setOnClickListener(v -> openResults("free online courses", "free_course"));
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyLanguageUi();
    }

    private void applyLanguageUi() {
        tvHelloLabel.setText(LanguageHelper.murahoLabel(this));
        tvHelloName.setText(SessionManager.getFirstName(this));

        LanguageHelper.applySearchScreen(
                this,
                etSearch,
                tvVerifiedSubtitle,
                findViewById(R.id.tvHowItWorksTitle),
                findViewById(R.id.tvStep1),
                findViewById(R.id.tvStep2),
                findViewById(R.id.tvStep3),
                findViewById(R.id.tvStep4),
                findViewById(R.id.chipAll),
                findViewById(R.id.chipScholarships),
                findViewById(R.id.chipJobs),
                findViewById(R.id.chipInternships),
                findViewById(R.id.chipPrograms),
                findViewById(R.id.chipTraining),
                findViewById(R.id.chipCompetitions),
                findViewById(R.id.chipCourses)
        );
    }

    private void checkBackendConnection() {
        if (backendChecked) {
            return;
        }
        backendChecked = true;

        RetrofitClient.getApiService().health().enqueue(new retrofit2.Callback<HealthResponse>() {
            @Override
            public void onResponse(retrofit2.Call<HealthResponse> call,
                                   retrofit2.Response<HealthResponse> response) {
                if (!response.isSuccessful()) {
                    showBackendOfflineToast();
                }
            }

            @Override
            public void onFailure(retrofit2.Call<HealthResponse> call, Throwable t) {
                showBackendOfflineToast();
            }
        });
    }

    private void showBackendOfflineToast() {
        Toast.makeText(this, LanguageHelper.backendOfflineMessage(this), Toast.LENGTH_LONG).show();
    }

    private void submitSearch() {
        String query = etSearch.getText().toString().trim();
        String emptyMsg = InziraPrefs.isKinyarwanda(this)
                ? "Andika ibyo ushaka gushakisha"
                : "Please enter a search term";
        if (query.isEmpty()) {
            Toast.makeText(this, emptyMsg, Toast.LENGTH_SHORT).show();
            return;
        }
        openResults(query);
    }

    private void openResults(String query) {
        openResults(query, null);
    }

    private void openResults(String query, String category) {
        Intent intent = new Intent(SearchActivity.this, ResultsActivity.class);
        intent.putExtra("query", query);
        if (category != null) {
            intent.putExtra("category", category);
        }
        startActivity(intent);
    }
}
