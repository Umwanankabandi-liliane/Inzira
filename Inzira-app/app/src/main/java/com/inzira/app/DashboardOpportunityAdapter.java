package com.inzira.app;

import android.content.Intent;
import android.net.Uri;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class DashboardOpportunityAdapter extends RecyclerView.Adapter<DashboardOpportunityAdapter.ViewHolder> {

    private final List<OpportunityResult> results;
    private final android.content.Context context;

    public DashboardOpportunityAdapter(List<OpportunityResult> results, android.content.Context context) {
        this.results = results;
        this.context = context;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_dashboard_opportunity, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        OpportunityResult result = results.get(position);
        holder.tvTitle.setText(WebsiteDisplayHelper.opportunityTitle(result));
        holder.tvCategory.setText(WebsiteDisplayHelper.categoryLabel(result.category));
        holder.tvTrustScore.setText(WebsiteDisplayHelper.trustDecimal(result.trust_score));
        holder.tvUrl.setText(WebsiteDisplayHelper.opportunityEmployer(result));

        holder.cardRoot.setOnClickListener(v -> openDetail(result));
        holder.btnVisit.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(WebsiteDisplayHelper.applyUrl(result)));
            context.startActivity(intent);
        });
        holder.btnVisit.setText(InziraPrefs.isKinyarwanda(context) ? "Saba" : "Apply");
    }

    private void openDetail(OpportunityResult result) {
        Intent intent = new Intent(context, WebsiteDetailActivity.class);
        intent.putExtra("url", result.url);
        intent.putExtra("title", result.title);
        intent.putExtra("category", result.category);
        intent.putExtra("trust_score", result.trust_score);
        intent.putExtra("organization", result.organization);
        intent.putExtra("deadline", result.deadline);
        intent.putExtra("eligibility", result.eligibility);
        intent.putExtra("location", result.location);
        intent.putExtra("apply_link", result.apply_link);
        intent.putExtra("snippet", result.snippet);
        context.startActivity(intent);
    }

    @Override
    public int getItemCount() {
        return results.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        View cardRoot;
        TextView tvTitle, tvUrl, tvCategory, tvTrustScore, btnVisit;

        ViewHolder(View itemView) {
            super(itemView);
            cardRoot = itemView.findViewById(R.id.cardRoot);
            tvTitle = itemView.findViewById(R.id.tvTitle);
            tvUrl = itemView.findViewById(R.id.tvUrl);
            tvCategory = itemView.findViewById(R.id.tvCategory);
            tvTrustScore = itemView.findViewById(R.id.tvTrustScore);
            btnVisit = itemView.findViewById(R.id.btnVisit);
        }
    }
}
