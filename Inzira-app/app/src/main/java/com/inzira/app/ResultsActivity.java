package com.inzira.app;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ResultsActivity extends AppCompatActivity {

    private TextView tvResultsTitle;
    private TextView tvResultsCount;
    private TextView tvEmpty;
    private ProgressBar progressBar;
    private RecyclerView recyclerView;
    private SwipeRefreshLayout swipeRefresh;

    private TextView chipAll;
    private TextView chipScholarships;
    private TextView chipPrograms;
    private TextView chipJobs;

    private String query = "";
    private String category = null;
    private final List<OpportunityResult> results = new ArrayList<>();
    private OpportunityAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        tvResultsTitle = findViewById(R.id.tvResultsTitle);
        tvResultsCount = findViewById(R.id.tvResultsCount);
        tvEmpty        = findViewById(R.id.tvEmpty);
        progressBar    = findViewById(R.id.progressBar);
        recyclerView   = findViewById(R.id.recyclerView);
        swipeRefresh   = findViewById(R.id.swipeRefresh);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        chipAll          = findViewById(R.id.chipFilterAll);
        chipScholarships = findViewById(R.id.chipFilterScholarships);
        chipPrograms     = findViewById(R.id.chipFilterPrograms);
        chipJobs         = findViewById(R.id.chipFilterJobs);

        query = getIntent().getStringExtra("query");
        if (query == null) {
            query = "";
        }
        category = getIntent().getStringExtra("category");
        updateTitle();

        adapter = new OpportunityAdapter(results, this);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        recyclerView.setAdapter(adapter);

        findViewById(R.id.btnBack).setOnClickListener(v -> finish());

        chipAll.setOnClickListener(v -> applyFilter(null, chipAll));
        chipScholarships.setOnClickListener(v -> applyFilter("scholarship", chipScholarships));
        chipPrograms.setOnClickListener(v -> applyFilter("program", chipPrograms));
        chipJobs.setOnClickListener(v -> applyFilter("job", chipJobs));
        highlightChip(chipAll);

        swipeRefresh.setOnRefreshListener(() -> startSearch(query));

        NavHelper.wireBottomNav(this, bottomNav, R.id.navDashboard);

        if (!query.isEmpty()) {
            startSearch(query);
        } else {
            showEmptyState();
        }
    }

    private void applyFilter(String newCategory, TextView activeChip) {
        category = newCategory;
        highlightChip(activeChip);
        if (!query.isEmpty()) {
            startSearch(query);
        }
    }

    private void highlightChip(TextView active) {
        TextView[] chips = {chipAll, chipScholarships, chipPrograms, chipJobs};
        for (TextView chip : chips) {
            boolean isActive = chip == active;
            chip.setBackgroundResource(isActive ? R.drawable.bg_filter_chip_active : R.drawable.bg_filter_chip);
            chip.setTextColor(isActive ? getColor(R.color.primary_dark_blue) : getColor(R.color.text_secondary));
            chip.setTypeface(chip.getTypeface(), isActive
                    ? android.graphics.Typeface.BOLD
                    : android.graphics.Typeface.NORMAL);
        }
    }

    private void updateTitle() {
        String title = query.isEmpty() ? "Search results" : capitalizeWords(query) + " Rwanda";
        tvResultsTitle.setText(title);
    }

    private String capitalizeWords(String raw) {
        String[] parts = raw.trim().split("\\s+");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            String p = parts[i];
            if (!p.isEmpty()) {
                sb.append(Character.toUpperCase(p.charAt(0)));
                if (p.length() > 1) {
                    sb.append(p.substring(1));
                }
            }
            if (i < parts.length - 1) {
                sb.append(' ');
            }
        }
        return sb.toString();
    }

    private void startSearch(String newQuery) {
        if (newQuery.isEmpty()) {
            Toast.makeText(this, "Please enter a search term", Toast.LENGTH_SHORT).show();
            swipeRefresh.setRefreshing(false);
            return;
        }

        query = newQuery;
        updateTitle();
        showLoading();

        SearchRequest request = SearchRequest.withDistrict(
                ResultsActivity.this, query, category, 25);
        RetrofitClient.getApiService().search(request).enqueue(new Callback<SearchResponse>() {
            @Override
            public void onResponse(Call<SearchResponse> call, Response<SearchResponse> response) {
                swipeRefresh.setRefreshing(false);
                progressBar.setVisibility(View.GONE);

                results.clear();
                if (response.isSuccessful() && response.body() != null && response.body().results != null) {
                    results.addAll(response.body().results);
                    sortByTrust();
                }
                adapter.notifyDataSetChanged();

                int count = results.size();
                if (count == 0) {
                    tvResultsCount.setText(LanguageHelper.noVerifiedWebsitesYet(ResultsActivity.this));
                } else {
                    tvResultsCount.setText(count + " verified websites found · AI-verified");
                }

                if (results.isEmpty()) {
                    showEmptyState();
                } else {
                    tvEmpty.setVisibility(View.GONE);
                    recyclerView.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<SearchResponse> call, Throwable t) {
                swipeRefresh.setRefreshing(false);
                progressBar.setVisibility(View.GONE);
                results.clear();
                adapter.notifyDataSetChanged();
                tvResultsCount.setText(LanguageHelper.backendUnavailableResults(ResultsActivity.this));
                showEmptyState();
                Toast.makeText(ResultsActivity.this,
                        LanguageHelper.backendOfflineMessage(ResultsActivity.this),
                        Toast.LENGTH_LONG).show();
            }
        });
    }

    private void sortByTrust() {
        Collections.sort(results, (a, b) -> Float.compare(b.trust_score, a.trust_score));
    }

    private void showLoading() {
        progressBar.setVisibility(View.VISIBLE);
        tvEmpty.setVisibility(View.GONE);
        recyclerView.setVisibility(View.GONE);
        tvResultsCount.setText(LanguageHelper.searchingWebsites(this));
    }

    private void showEmptyState() {
        tvEmpty.setVisibility(View.VISIBLE);
        recyclerView.setVisibility(View.GONE);
    }
}
