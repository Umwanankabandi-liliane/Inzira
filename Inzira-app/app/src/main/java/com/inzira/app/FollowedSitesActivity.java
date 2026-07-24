package com.inzira.app;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageButton;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class FollowedSitesActivity extends AppCompatActivity {

    private TextView tvSiteCount;
    private TextView tvEmpty;
    private RecyclerView recyclerView;
    private final List<Map<String, Object>> sites = new ArrayList<>();
    private FollowedSitesAdapter adapter;
    private ValueEventListener sitesListener;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_followed_sites);

        tvSiteCount   = findViewById(R.id.tvSiteCount);
        tvEmpty       = findViewById(R.id.tvEmpty);
        recyclerView  = findViewById(R.id.recyclerView);
        ImageButton btnAdd = findViewById(R.id.btnAdd);
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);

        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new FollowedSitesAdapter(sites, site -> {
            String url = site.get("url") != null ? site.get("url").toString() : "";
            if (!url.isEmpty()) {
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
            }
        });
        recyclerView.setAdapter(adapter);

        btnAdd.setOnClickListener(v ->
                startActivity(new Intent(FollowedSitesActivity.this, SearchActivity.class)));

        NavHelper.wireBottomNav(this, bottomNav, R.id.navMatches);

        loadFollowedSites();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        String uid = FirebaseAuth.getInstance().getCurrentUser() != null
                ? FirebaseAuth.getInstance().getCurrentUser().getUid() : null;
        if (uid != null && sitesListener != null) {
            FirebaseDatabase.getInstance().getReference("followed_sites")
                    .child(uid)
                    .removeEventListener(sitesListener);
        }
    }

    private void loadFollowedSites() {
        String uid = FirebaseAuth.getInstance().getCurrentUser() != null
                ? FirebaseAuth.getInstance().getCurrentUser().getUid() : null;
        if (uid == null) {
            tvSiteCount.setText("0 websites");
            showEmptyState();
            return;
        }

        sitesListener = new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot snapshot) {
                sites.clear();
                for (DataSnapshot child : snapshot.getChildren()) {
                    Object value = child.getValue();
                    if (value instanceof Map) {
                        @SuppressWarnings("unchecked")
                        Map<String, Object> map = new HashMap<>((Map<String, Object>) value);
                        sites.add(map);
                    }
                }
                adapter.notifyDataSetChanged();
                updateUi();
            }

            @Override
            public void onCancelled(DatabaseError error) {
                tvSiteCount.setText("0 websites");
                showEmptyState();
            }
        };

        FirebaseDatabase.getInstance().getReference("followed_sites")
                .child(uid)
                .addValueEventListener(sitesListener);
    }

    private void updateUi() {
        int count = sites.size();
        int alertsOn = 0;
        for (Map<String, Object> site : sites) {
            Object notify = site.get("notifyEnabled");
            if (notify instanceof Boolean && (Boolean) notify) {
                alertsOn++;
            }
        }
        tvSiteCount.setText(count
                + (count == 1 ? " website" : " websites")
                + " · alerts on for "
                + alertsOn);
        if (sites.isEmpty()) {
            showEmptyState();
        } else {
            tvEmpty.setVisibility(View.GONE);
            recyclerView.setVisibility(View.VISIBLE);
        }
    }

    private void showEmptyState() {
        tvEmpty.setVisibility(View.VISIBLE);
        recyclerView.setVisibility(View.GONE);
    }
}
