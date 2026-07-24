package com.inzira.app;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.FirebaseDatabase;
import java.util.HashMap;
import java.util.Map;

public class WebsiteDetailActivity extends AppCompatActivity {

    private String url;
    private String title;
    private String category;
    private boolean following;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_website_detail);

        url          = nullToEmpty(getIntent().getStringExtra("url"));
        title        = nullToEmpty(getIntent().getStringExtra("title"));
        category     = nullToEmpty(getIntent().getStringExtra("category"));
        float trustScore = getIntent().getFloatExtra("trust_score", 0f);
        String organization = nullToEmpty(getIntent().getStringExtra("organization"));
        String deadline     = nullToEmpty(getIntent().getStringExtra("deadline"));
        String eligibility  = nullToEmpty(getIntent().getStringExtra("eligibility"));
        String location     = nullToEmpty(getIntent().getStringExtra("location"));
        String snippet      = nullToEmpty(getIntent().getStringExtra("snippet"));

        OpportunityResult result = new OpportunityResult();
        result.url = url;
        result.title = title;
        result.category = category;
        result.trust_score = trustScore;
        result.organization = organization;
        result.deadline = deadline;
        result.eligibility = eligibility;
        result.location = location;
        result.snippet = snippet;

        ImageButton btnBack = findViewById(R.id.btnBack);
        TextView tvTitle = findViewById(R.id.tvTitle);
        TextView tvUrl = findViewById(R.id.tvUrl);
        TextView tvTrustBadge = findViewById(R.id.tvTrustBadge);
        TextView tvAiSummary = findViewById(R.id.tvAiSummary);
        LinearLayout containerFacts = findViewById(R.id.containerFacts);
        Button btnVisitWebsite = findViewById(R.id.btnVisitWebsite);
        ImageButton btnSave = findViewById(R.id.btnSave);
        ImageButton btnNotify = findViewById(R.id.btnNotify);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        btnBack.setOnClickListener(v -> finish());

        String displayName = WebsiteDisplayHelper.websiteName(result);
        tvTitle.setText(displayName);
        tvUrl.setText(extractDomain(url));
        tvTrustBadge.setText("Trust score: " + WebsiteDisplayHelper.trustDecimal(trustScore));
        tvAiSummary.setText(WebsiteDisplayHelper.aiSummary(result));

        bindFacts(containerFacts, result);

        btnVisitWebsite.setOnClickListener(v -> openWebsite(url));
        btnSave.setOnClickListener(v -> toggleFollow(btnSave, btnNotify));
        btnNotify.setOnClickListener(v -> toggleFollow(btnSave, btnNotify));

        bottomNav.setSelectedItemId(R.id.navDashboard);
        NavHelper.wireBottomNav(this, bottomNav, R.id.navDashboard);

        refreshFollowUi(btnSave, btnNotify);
    }

    private void bindFacts(LinearLayout container, OpportunityResult result) {
        container.removeAllViews();
        addFactRow(container, R.color.medium_blue, "Category",
                WebsiteDisplayHelper.categoryLabel(result.category));
        addFactRow(container, 0xFFE65100, "Deadline",
                !TextUtils.isEmpty(result.deadline) ? result.deadline : "Check website");
        addFactRow(container, 0xFF2E7D32, "Eligibility",
                !TextUtils.isEmpty(result.eligibility) ? result.eligibility : "See website");
        addFactRow(container, 0xFF00838F, "Location",
                !TextUtils.isEmpty(result.location) ? result.location : "Rwanda · Africa");
        addFactRow(container, 0xFF6A1B9A, "Benefit",
                WebsiteDisplayHelper.benefitLine(result));
    }

    private void addFactRow(LinearLayout container, int iconColor, String label, String value) {
        View row = LayoutInflater.from(this).inflate(R.layout.item_detail_fact_row, container, false);
        View dot = row.findViewById(R.id.iconDot);
        TextView tvLabel = row.findViewById(R.id.tvLabel);
        TextView tvValue = row.findViewById(R.id.tvValue);
        dot.setBackgroundTintList(android.content.res.ColorStateList.valueOf(iconColor));
        tvLabel.setText(label);
        tvValue.setText(value);
        container.addView(row);
    }

    private void openWebsite(String websiteUrl) {
        if (websiteUrl.isEmpty()) {
            Toast.makeText(this, "URL not available", Toast.LENGTH_SHORT).show();
            return;
        }
        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(websiteUrl)));
    }

    private void refreshFollowUi(ImageButton btnSave, ImageButton btnNotify) {
        String uid = FirebaseAuth.getInstance().getCurrentUser() != null
                ? FirebaseAuth.getInstance().getCurrentUser().getUid() : null;
        if (uid == null || url.isEmpty()) {
            following = false;
            updateFollowButtons(btnSave, btnNotify);
            return;
        }

        String siteId = String.valueOf(url.hashCode());
        FirebaseDatabase.getInstance().getReference("followed_sites")
                .child(uid)
                .child(siteId)
                .get()
                .addOnSuccessListener(snapshot -> {
                    following = snapshot.exists();
                    updateFollowButtons(btnSave, btnNotify);
                });
    }

    private void toggleFollow(ImageButton btnSave, ImageButton btnNotify) {
        String uid = FirebaseAuth.getInstance().getCurrentUser() != null
                ? FirebaseAuth.getInstance().getCurrentUser().getUid() : null;
        if (uid == null) {
            Toast.makeText(this, "Please sign in to save websites", Toast.LENGTH_SHORT).show();
            return;
        }
        if (url.isEmpty()) {
            Toast.makeText(this, "URL not available", Toast.LENGTH_SHORT).show();
            return;
        }

        String siteId = String.valueOf(url.hashCode());
        com.google.firebase.database.DatabaseReference ref =
                FirebaseDatabase.getInstance().getReference("followed_sites")
                        .child(uid)
                        .child(siteId);

        ref.get().addOnSuccessListener(snapshot -> {
            if (snapshot.exists()) {
                ref.removeValue();
                following = false;
                BackendSyncHelper.removeSite(this, BackendSyncHelper.domainOf(url));
                Toast.makeText(this, "Removed from saved websites", Toast.LENGTH_SHORT).show();
            } else {
                Map<String, Object> data = new HashMap<>();
                data.put("url", url);
                data.put("title", title);
                data.put("category", category);
                data.put("siteId", siteId);
                data.put("followedAt", System.currentTimeMillis());
                data.put("notifyEnabled", true);
                ref.setValue(data);
                following = true;
                BackendSyncHelper.saveSite(this, url, title, category, true);
                PushRegistrar.registerIfLoggedIn();
                Toast.makeText(this, "Saved — alerts enabled for this website",
                        Toast.LENGTH_SHORT).show();
            }
            updateFollowButtons(btnSave, btnNotify);
        });
    }

    private void updateFollowButtons(ImageButton btnSave, ImageButton btnNotify) {
        int saveTint = following ? R.color.primary_dark_blue : R.color.text_primary;
        btnSave.setColorFilter(getColor(saveTint));
        btnNotify.setColorFilter(getColor(following ? R.color.primary_dark_blue : R.color.text_primary));
    }

    private String extractDomain(String websiteUrl) {
        try {
            return websiteUrl.replace("https://", "")
                    .replace("http://", "")
                    .split("/")[0];
        } catch (Exception e) {
            return websiteUrl;
        }
    }

    private String nullToEmpty(String value) {
        return value == null ? "" : value;
    }
}
