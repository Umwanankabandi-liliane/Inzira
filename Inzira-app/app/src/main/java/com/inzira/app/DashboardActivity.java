package com.inzira.app;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.gson.Gson;
import java.util.ArrayList;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class DashboardActivity extends AppCompatActivity {

    private WebView mapWebView;
    private TextView tvSelectedDistrict;
    private TextView tvDistrictCount;
    private TextView tvDistrictLabel;
    private TextView tvMapHint;
    private TextView tvLegendLow;
    private TextView tvLegendHigh;
    private TextView tvEmptyDistrict;
    private ProgressBar progressDistrict;
    private RecyclerView recyclerOpportunities;
    private final List<OpportunityResult> districtResults = new ArrayList<>();
    private DashboardOpportunityAdapter adapter;
    private String selectedDistrict = null;
    private boolean mapReady = false;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!SessionManager.isLoggedIn(this)) {
            NavHelper.openLogin(this, false, false);
            finish();
            return;
        }

        setContentView(R.layout.activity_dashboard);
        SessionManager.syncFirebaseProfile(this);

        mapWebView = findViewById(R.id.mapWebView);
        tvSelectedDistrict = findViewById(R.id.tvSelectedDistrict);
        tvDistrictCount = findViewById(R.id.tvDistrictCount);
        tvDistrictLabel = findViewById(R.id.tvDistrictLabel);
        tvMapHint = findViewById(R.id.tvMapHint);
        tvLegendLow = findViewById(R.id.tvLegendLow);
        tvLegendHigh = findViewById(R.id.tvLegendHigh);
        tvEmptyDistrict = findViewById(R.id.tvEmptyDistrict);
        progressDistrict = findViewById(R.id.progressDistrict);
        recyclerOpportunities = findViewById(R.id.recyclerOpportunities);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        applyLanguageUi();
        showEmptyState();

        WebSettings settings = mapWebView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        mapWebView.setBackgroundColor(0xFFF6F8FB);
        mapWebView.addJavascriptInterface(new MapBridge(), "AndroidBridge");
        mapWebView.loadUrl("file:///android_asset/rwanda_map.html");
        mapWebView.setWebViewClient(new android.webkit.WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                mapReady = true;
                loadRadarData();
            }
        });

        adapter = new DashboardOpportunityAdapter(districtResults, this);
        recyclerOpportunities.setLayoutManager(
                new LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false));
        recyclerOpportunities.setAdapter(adapter);

        NavHelper.wireBottomNav(this, bottomNav, R.id.navDashboard);
        loadRadarData();
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyLanguageUi();
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        NavHelper.localizeBottomNav(this, bottomNav);
        if (selectedDistrict != null) {
            tvSelectedDistrict.setText(DistrictHelper.displayName(this, selectedDistrict));
        }
    }

    private void applyLanguageUi() {
        tvDistrictLabel.setText(LanguageHelper.dashboardOpportunitiesLabel(this));
        tvMapHint.setText(LanguageHelper.dashboardMapHint(this));
        tvLegendLow.setText(LanguageHelper.legendLow(this));
        tvLegendHigh.setText(LanguageHelper.legendHigh(this));
        if (selectedDistrict == null) {
            tvSelectedDistrict.setText(LanguageHelper.dashboardTapDistrict(this));
        }
        tvEmptyDistrict.setText(LanguageHelper.dashboardSelectDistrict(this));
    }

    private void showEmptyState() {
        recyclerOpportunities.setVisibility(View.GONE);
        tvEmptyDistrict.setVisibility(View.VISIBLE);
        tvDistrictCount.setVisibility(View.GONE);
    }

    private void showResultsState(int count) {
        recyclerOpportunities.setVisibility(View.VISIBLE);
        tvEmptyDistrict.setVisibility(View.GONE);
        tvDistrictCount.setVisibility(View.VISIBLE);
        tvDistrictCount.setText(LanguageHelper.dashboardSitesCount(this, count));
    }

    private void loadRadarData() {
        RetrofitClient.getApiService().youthRadar().enqueue(new Callback<YouthRadarResponse>() {
            @Override
            public void onResponse(Call<YouthRadarResponse> call, Response<YouthRadarResponse> response) {
                if (!mapReady || !response.isSuccessful() || response.body() == null) {
                    return;
                }
                String json = new Gson().toJson(response.body().districts);
                mapWebView.evaluateJavascript("setRadarData(" + json + ")", null);
            }

            @Override
            public void onFailure(Call<YouthRadarResponse> call, Throwable t) {
                // Map still works with default colors
            }
        });
    }

    private void onDistrictSelected(String district) {
        selectedDistrict = district;
        tvSelectedDistrict.setText(DistrictHelper.displayName(this, district));
        loadDistrictOpportunities(district);
    }

    private void loadDistrictOpportunities(String district) {
        progressDistrict.setVisibility(View.VISIBLE);
        districtResults.clear();
        adapter.notifyDataSetChanged();
        showEmptyState();

        RetrofitClient.getApiService().registryOpportunities(50, null, district, null)
                .enqueue(new Callback<RegistryOpportunitiesResponse>() {
            @Override
            public void onResponse(Call<RegistryOpportunitiesResponse> call,
                                   Response<RegistryOpportunitiesResponse> response) {
                progressDistrict.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null
                        && response.body().opportunities != null) {
                    districtResults.addAll(response.body().opportunities);
                    adapter.notifyDataSetChanged();
                    if (districtResults.isEmpty()) {
                        showEmptyState();
                        tvEmptyDistrict.setText(LanguageHelper.dashboardNoSites(DashboardActivity.this));
                    } else {
                        showResultsState(districtResults.size());
                    }
                } else {
                    showEmptyState();
                    Toast.makeText(DashboardActivity.this,
                            LanguageHelper.backendUnavailableResults(DashboardActivity.this),
                            Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<RegistryOpportunitiesResponse> call, Throwable t) {
                progressDistrict.setVisibility(View.GONE);
                showEmptyState();
                Toast.makeText(DashboardActivity.this,
                        LanguageHelper.backendOfflineMessage(DashboardActivity.this),
                        Toast.LENGTH_LONG).show();
            }
        });
    }

    private class MapBridge {
        @JavascriptInterface
        public void onDistrictTap(String district) {
            runOnUiThread(() -> onDistrictSelected(district));
        }
    }
}
