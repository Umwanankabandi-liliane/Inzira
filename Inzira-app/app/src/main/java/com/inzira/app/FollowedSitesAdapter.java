package com.inzira.app;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Switch;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.FirebaseDatabase;
import java.util.List;
import java.util.Map;

public class FollowedSitesAdapter extends RecyclerView.Adapter<FollowedSitesAdapter.ViewHolder> {

    public interface OnVisitListener {
        void onVisit(Map<String, Object> site);
    }

    private final List<Map<String, Object>> sites;
    private final OnVisitListener onVisit;

    public FollowedSitesAdapter(List<Map<String, Object>> sites, OnVisitListener onVisit) {
        this.sites = sites;
        this.onVisit = onVisit;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_followed_site, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        Map<String, Object> site = sites.get(position);
        String url      = stringValue(site.get("url"));
        String title    = stringValue(site.get("title"));
        String category = stringValue(site.get("category"));
        String siteId   = stringValue(site.get("siteId"));
        if (siteId.isEmpty()) {
            siteId = String.valueOf(url.hashCode());
        }

        boolean notifyOn = true;
        Object notifyValue = site.get("notifyEnabled");
        if (notifyValue instanceof Boolean) {
            notifyOn = (Boolean) notifyValue;
        }

        holder.tvTitle.setText(title.isEmpty() ? "Website" : title);
        holder.tvUrl.setText(extractDomain(url));
        holder.tvCategory.setText(formatCategory(category));

        holder.switchNotify.setOnCheckedChangeListener(null);
        holder.switchNotify.setChecked(notifyOn);

        String finalSiteId = siteId;
        holder.switchNotify.setOnCheckedChangeListener((buttonView, isChecked) -> {
            String uid = FirebaseAuth.getInstance().getCurrentUser() != null
                    ? FirebaseAuth.getInstance().getCurrentUser().getUid() : null;
            if (uid == null) {
                return;
            }
            FirebaseDatabase.getInstance().getReference("followed_sites")
                    .child(uid)
                    .child(finalSiteId)
                    .child("notifyEnabled")
                    .setValue(isChecked);
        });

        holder.tvVisit.setOnClickListener(v -> onVisit.onVisit(site));

        holder.tvUnfollow.setOnClickListener(v -> {
            String uid = FirebaseAuth.getInstance().getCurrentUser() != null
                    ? FirebaseAuth.getInstance().getCurrentUser().getUid() : null;
            if (uid == null) {
                return;
            }
            FirebaseDatabase.getInstance().getReference("followed_sites")
                    .child(uid)
                    .child(finalSiteId)
                    .removeValue();
        });
    }

    @Override
    public int getItemCount() {
        return sites.size();
    }

    private String stringValue(Object value) {
        return value != null ? value.toString() : "";
    }

    private String extractDomain(String url) {
        return url.replace("https://", "").replace("http://", "").split("/")[0];
    }

    private String formatCategory(String category) {
        if (category.isEmpty()) {
            return "General";
        }
        return category.replace("_", " ");
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvTitle;
        TextView tvUrl;
        TextView tvCategory;
        Switch switchNotify;
        TextView tvVisit;
        TextView tvUnfollow;

        ViewHolder(View itemView) {
            super(itemView);
            tvTitle      = itemView.findViewById(R.id.tvTitle);
            tvUrl        = itemView.findViewById(R.id.tvUrl);
            tvCategory   = itemView.findViewById(R.id.tvCategory);
            switchNotify = itemView.findViewById(R.id.switchNotify);
            tvVisit      = itemView.findViewById(R.id.tvVisit);
            tvUnfollow   = itemView.findViewById(R.id.tvUnfollow);
        }
    }
}
