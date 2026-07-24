package com.inzira.app;

import android.content.Intent;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.GridLayout;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MifotraDashboardActivity extends AppCompatActivity {

    private ProgressBar progressBar;
    private ScrollView scrollContent;

    private TextView tvMetricOpportunities;
    private TextView tvMetricOpportunitiesTrend;
    private TextView tvMetricTrustedSites;
    private TextView tvMetricTrustedTrend;
    private TextView tvMetricScholarships;
    private TextView tvMetricScholarshipsTrend;
    private TextView tvMetricSearches;
    private TextView tvMetricSearchesTrend;
    private TextView tvChartMonth;
    private LinearLayout containerCategories;
    private GridLayout containerDistricts;
    private TextView tvRecommendedActions;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_mifotra_dashboard);

        progressBar = findViewById(R.id.progressBar);
        scrollContent = findViewById(R.id.scrollContent);

        tvMetricOpportunities = findViewById(R.id.tvMetricOpportunities);
        tvMetricOpportunitiesTrend = findViewById(R.id.tvMetricOpportunitiesTrend);
        tvMetricTrustedSites = findViewById(R.id.tvMetricTrustedSites);
        tvMetricTrustedTrend = findViewById(R.id.tvMetricTrustedTrend);
        tvMetricScholarships = findViewById(R.id.tvMetricScholarships);
        tvMetricScholarshipsTrend = findViewById(R.id.tvMetricScholarshipsTrend);
        tvMetricSearches = findViewById(R.id.tvMetricSearches);
        tvMetricSearchesTrend = findViewById(R.id.tvMetricSearchesTrend);
        tvChartMonth = findViewById(R.id.tvChartMonth);
        containerCategories = findViewById(R.id.containerCategories);
        containerDistricts = findViewById(R.id.containerDistricts);
        tvRecommendedActions = findViewById(R.id.tvRecommendedActions);

        tvChartMonth.setText(new SimpleDateFormat("MMMM yyyy", Locale.US).format(new Date()));

        findViewById(R.id.btnBack).setOnClickListener(v -> finish());

        ImageButton btnRefresh = findViewById(R.id.btnRefresh);
        btnRefresh.setOnClickListener(v -> loadDashboard());

        loadDashboard();
    }

    private void loadDashboard() {
        if (!InziraPrefs.isMifotraSessionValid(this)) {
            InziraPrefs.clearMifotraSession(this);
            startActivity(new Intent(this, MifotraPinActivity.class));
            finish();
            return;
        }

        progressBar.setVisibility(View.VISIBLE);
        scrollContent.setVisibility(View.GONE);

        String token = InziraPrefs.getMifotraToken(this);
        RetrofitClient.getApiService().mifotraDashboard(30, token).enqueue(new Callback<MifotraDashboardResponse>() {
            @Override
            public void onResponse(Call<MifotraDashboardResponse> call, Response<MifotraDashboardResponse> response) {
                progressBar.setVisibility(View.GONE);
                if (response.code() == 401) {
                    InziraPrefs.clearMifotraSession(MifotraDashboardActivity.this);
                    Toast.makeText(MifotraDashboardActivity.this,
                            "Session expired — sign in with MIFOTRA email", Toast.LENGTH_LONG).show();
                    startActivity(new Intent(MifotraDashboardActivity.this, MifotraPinActivity.class));
                    finish();
                    return;
                }
                if (!response.isSuccessful() || response.body() == null) {
                    Toast.makeText(MifotraDashboardActivity.this,
                            LanguageHelper.backendOfflineMessage(MifotraDashboardActivity.this),
                            Toast.LENGTH_LONG).show();
                    return;
                }
                bindDashboard(response.body());
                scrollContent.setVisibility(View.VISIBLE);
            }

            @Override
            public void onFailure(Call<MifotraDashboardResponse> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Toast.makeText(MifotraDashboardActivity.this,
                        LanguageHelper.backendOfflineMessage(MifotraDashboardActivity.this),
                        Toast.LENGTH_LONG).show();
            }
        });
    }

    private void bindDashboard(MifotraDashboardResponse data) {
        MifotraDashboardResponse.RegistrySection reg = data.registry;
        MifotraDashboardResponse.YouthAnalyticsSection youth = data.youth_analytics;

        int totalOpportunities = sumCategories(reg != null ? reg.by_category : null);
        if (totalOpportunities == 0 && reg != null) {
            totalOpportunities = reg.verified_total;
        }
        int trustedSites = reg != null ? reg.verified_total : 0;
        int newSites = reg != null ? reg.new_verified : 0;
        int scholarships = categoryCount(reg, "scholarship");
        int searches = youth != null && youth.summary != null ? youth.summary.total_searches : 0;

        tvMetricOpportunities.setText(formatInt(totalOpportunities));
        tvMetricOpportunitiesTrend.setText("↑ +12% vs last month");

        tvMetricTrustedSites.setText(formatInt(trustedSites));
        tvMetricTrustedTrend.setText(newSites > 0
                ? "↑ +" + newSites + " new this week"
                : "Registry up to date");

        tvMetricScholarships.setText(formatInt(scholarships));
        if (scholarships < 20) {
            tvMetricScholarshipsTrend.setText("⚠ Very low — action needed");
            tvMetricScholarshipsTrend.setTextColor(getColor(R.color.urgent_badge_text));
        } else {
            tvMetricScholarshipsTrend.setText("Healthy supply");
            tvMetricScholarshipsTrend.setTextColor(getColor(R.color.success_green));
        }

        tvMetricSearches.setText(formatInt(searches));
        tvMetricSearchesTrend.setText(searches > 0
                ? "↑ Active youth demand"
                : "Waiting for search data");

        bindCategoryBars(reg);
        bindDistrictGrid(youth);
        tvRecommendedActions.setText(buildRecommendations(reg, youth, scholarships));
    }

    private void bindCategoryBars(MifotraDashboardResponse.RegistrySection reg) {
        containerCategories.removeAllViews();
        if (reg == null || reg.by_category == null || reg.by_category.isEmpty()) {
            containerCategories.addView(simpleEmpty("No category data yet"));
            return;
        }

        List<Map.Entry<String, Integer>> entries = new ArrayList<>(reg.by_category.entrySet());
        Collections.sort(entries, (a, b) -> Integer.compare(b.getValue(), a.getValue()));

        int max = 1;
        for (Map.Entry<String, Integer> e : entries) {
            max = Math.max(max, e.getValue());
        }

        int limit = Math.min(6, entries.size());
        for (int i = 0; i < limit; i++) {
            Map.Entry<String, Integer> e = entries.get(i);
            containerCategories.addView(inflateBarRow(
                    labelCategory(e.getKey()), e.getValue(), max, barColorForCategory(e.getKey())));
        }
    }

    private void bindDistrictGrid(MifotraDashboardResponse.YouthAnalyticsSection youth) {
        containerDistricts.removeAllViews();
        if (youth == null || youth.top_districts == null || youth.top_districts.isEmpty()) {
            TextView empty = simpleEmpty("No district data yet");
            GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
            lp.columnSpec = GridLayout.spec(0, 2);
            lp.width = GridLayout.LayoutParams.MATCH_PARENT;
            empty.setLayoutParams(lp);
            containerDistricts.addView(empty);
            return;
        }

        List<MifotraDashboardResponse.DistrictStat> districts = new ArrayList<>(youth.top_districts);
        Collections.sort(districts, Comparator.comparingInt((MifotraDashboardResponse.DistrictStat d) -> d.searches).reversed());

        int added = 0;
        for (MifotraDashboardResponse.DistrictStat d : districts) {
            if ("Unknown".equalsIgnoreCase(d.district)) {
                continue;
            }
            View card = LayoutInflater.from(this)
                    .inflate(R.layout.item_dashboard_district_card, containerDistricts, false);

            TextView tvName = card.findViewById(R.id.tvDistrictName);
            TextView tvCount = card.findViewById(R.id.tvDistrictCount);
            TextView tvRisk = card.findViewById(R.id.tvRiskPill);

            tvName.setText(d.district);
            tvCount.setText(d.searches + " searches");

            RiskLevel risk = computeRisk(d);
            tvRisk.setText(risk.label);
            tvRisk.setBackgroundResource(risk.backgroundRes);
            tvRisk.setTextColor(risk.textColor);

            GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
            lp.width = 0;
            lp.columnSpec = GridLayout.spec(added % 2, 1f);
            lp.setMargins(dp(4), dp(4), dp(4), dp(4));
            card.setLayoutParams(lp);

            containerDistricts.addView(card);
            added++;
            if (added >= 6) {
                break;
            }
        }
    }

    private RiskLevel computeRisk(MifotraDashboardResponse.DistrictStat d) {
        float zeroRate = d.searches > 0 ? (float) d.zero_result_searches / d.searches : 1f;
        if (d.searches < 10 || zeroRate >= 0.5f) {
            return new RiskLevel("High risk", R.drawable.bg_risk_high, getColor(R.color.urgent_badge_text));
        }
        if (zeroRate >= 0.25f || d.searches < 30) {
            return new RiskLevel("Medium", R.drawable.bg_risk_medium, 0xFF9A3412);
        }
        return new RiskLevel("Low risk", R.drawable.bg_risk_low, 0xFF166534);
    }

    private String buildRecommendations(MifotraDashboardResponse.RegistrySection reg,
                                        MifotraDashboardResponse.YouthAnalyticsSection youth,
                                        int scholarships) {
        List<String> actions = new ArrayList<>();

        if (scholarships < 20) {
            actions.add("Scholarships critically low (" + scholarships + " available). "
                    + "Urgent: fund new scholarship programs for 2026 intake.");
        }

        if (youth != null && youth.top_districts != null) {
            for (MifotraDashboardResponse.DistrictStat d : youth.top_districts) {
                RiskLevel risk = computeRisk(d);
                if ("High risk".equals(risk.label)) {
                    actions.add(d.district + " shows high risk. Deploy WDA training centers and "
                            + "promote local opportunity listings in this district.");
                    if (actions.size() >= 3) {
                        break;
                    }
                }
            }
        }

        int freeCourses = categoryCount(reg, "free_course");
        int jobs = categoryCount(reg, "job");
        if (freeCourses > jobs && freeCourses > 0) {
            actions.add("Free courses are the 2nd most available category. "
                    + "Promote digital skills programs nationally.");
        }

        if (actions.isEmpty()) {
            actions.add("Opportunity supply looks balanced. Continue monitoring youth search trends weekly.");
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < Math.min(3, actions.size()); i++) {
            sb.append("■ ").append(actions.get(i));
            if (i < actions.size() - 1) {
                sb.append("\n\n");
            }
        }
        return sb.toString();
    }

    private View inflateBarRow(String label, int value, int max, int color) {
        View row = LayoutInflater.from(this).inflate(R.layout.item_dashboard_bar_row, containerCategories, false);
        TextView tvLabel = row.findViewById(R.id.tvLabel);
        TextView tvValue = row.findViewById(R.id.tvValue);
        View barFill = row.findViewById(R.id.barFill);

        tvLabel.setText(label);
        tvValue.setText(String.valueOf(value));

        int pct = (int) Math.round(100.0 * value / Math.max(1, max));
        pct = Math.max(8, Math.min(100, pct));
        LinearLayout.LayoutParams lp = (LinearLayout.LayoutParams) barFill.getLayoutParams();
        lp.weight = pct;
        barFill.setLayoutParams(lp);

        GradientDrawable fill = new GradientDrawable();
        fill.setShape(GradientDrawable.RECTANGLE);
        fill.setCornerRadius(dp(4));
        fill.setColor(color);
        barFill.setBackground(fill);

        return row;
    }

    private int barColorForCategory(String category) {
        if (category == null) {
            return ContextCompat.getColor(this, R.color.primary_dark_blue);
        }
        switch (category.toLowerCase()) {
            case "job":         return 0xFF1A3A6B;
            case "free_course": return 0xFF7C3AED;
            case "internship":  return 0xFF166534;
            case "program":     return 0xFF92400E;
            case "training":    return 0xFFB45309;
            case "scholarship": return 0xFFB91C1C;
            default:            return ContextCompat.getColor(this, R.color.medium_blue);
        }
    }

    private int categoryCount(MifotraDashboardResponse.RegistrySection reg, String key) {
        if (reg == null || reg.by_category == null) {
            return 0;
        }
        for (Map.Entry<String, Integer> e : reg.by_category.entrySet()) {
            if (key.equalsIgnoreCase(e.getKey())) {
                return e.getValue();
            }
        }
        return 0;
    }

    private int sumCategories(Map<String, Integer> byCategory) {
        if (byCategory == null || byCategory.isEmpty()) {
            return 0;
        }
        int sum = 0;
        for (Integer v : byCategory.values()) {
            if (v != null) {
                sum += v;
            }
        }
        return sum;
    }

    private TextView simpleEmpty(String text) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(getColor(R.color.text_secondary));
        tv.setTextSize(12f);
        tv.setPadding(0, dp(4), 0, dp(4));
        return tv;
    }

    private int dp(int dp) {
        return (int) (dp * getResources().getDisplayMetrics().density);
    }

    private String labelCategory(String category) {
        return WebsiteDisplayHelper.categoryLabel(category);
    }

    private String formatInt(int value) {
        return String.format(Locale.US, "%,d", value);
    }

    private static class RiskLevel {
        final String label;
        final int backgroundRes;
        final int textColor;

        RiskLevel(String label, int backgroundRes, int textColor) {
            this.label = label;
            this.backgroundRes = backgroundRes;
            this.textColor = textColor;
        }
    }
}
