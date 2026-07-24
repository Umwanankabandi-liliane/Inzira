package com.inzira.app;

import android.content.Intent;
import android.net.Uri;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class OpportunityAdapter extends RecyclerView.Adapter<OpportunityAdapter.ViewHolder> {

    private final List<OpportunityResult> results;
    private final android.content.Context context;

    public OpportunityAdapter(List<OpportunityResult> results, android.content.Context context) {
        this.results = results;
        this.context = context;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_opportunity, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        OpportunityResult result = results.get(position);

        holder.tvTitle.setText(WebsiteDisplayHelper.opportunityTitle(result));
        holder.tvCategory.setText(WebsiteDisplayHelper.categoryLabel(result.category));

        holder.tvUrl.setText(WebsiteDisplayHelper.opportunityEmployer(result));

        int trust = WebsiteDisplayHelper.trustPercent(result.trust_score);
        holder.trustBar.setProgress(trust);
        holder.tvTrustScore.setText(WebsiteDisplayHelper.trustDecimal(result.trust_score));

        String funding = WebsiteDisplayHelper.fundingTag(result);
        if (!TextUtils.isEmpty(funding)) {
            holder.tvTagFunding.setText(funding);
            holder.tvTagFunding.setVisibility(View.VISIBLE);
        } else {
            holder.tvTagFunding.setVisibility(View.GONE);
        }

        String eligibility = WebsiteDisplayHelper.eligibilityTag(result);
        if (!TextUtils.isEmpty(eligibility)) {
            holder.tvTagEligibility.setText(eligibility);
            holder.tvTagEligibility.setVisibility(View.VISIBLE);
        } else {
            holder.tvTagEligibility.setVisibility(View.GONE);
        }

        holder.tvDeadline.setText(WebsiteDisplayHelper.deadlineLabel(result));

        int accentColor = accentForCategory(result.category);
        holder.iconContainer.setBackgroundTintList(
                android.content.res.ColorStateList.valueOf(context.getColor(accentColor)));

        Intent detailIntent = buildDetailIntent(result);
        holder.cardView.setOnClickListener(v -> context.startActivity(detailIntent));

        holder.tvVisit.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(WebsiteDisplayHelper.applyUrl(result)));
            context.startActivity(intent);
        });
    }

    private int accentForCategory(String category) {
        if (category == null) {
            return R.color.badge_blue_background;
        }
        switch (category.toLowerCase()) {
            case "job":         return R.color.badge_blue_background;
            case "scholarship": return R.color.badge_blue_background;
            case "program":     return R.color.badge_blue_background;
            default:            return R.color.badge_blue_background;
        }
    }

    private Intent buildDetailIntent(OpportunityResult result) {
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
        return intent;
    }

    @Override
    public int getItemCount() {
        return results.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        View cardView;
        FrameLayout iconContainer;
        TextView tvTitle, tvUrl, tvCategory, tvDeadline, tvTrustScore, tvVisit;
        TextView tvTagFunding, tvTagEligibility;
        ProgressBar trustBar;

        ViewHolder(View itemView) {
            super(itemView);
            cardView         = itemView.findViewById(R.id.cardView);
            iconContainer    = itemView.findViewById(R.id.iconContainer);
            tvTitle          = itemView.findViewById(R.id.tvTitle);
            tvUrl            = itemView.findViewById(R.id.tvUrl);
            tvCategory       = itemView.findViewById(R.id.tvCategory);
            tvDeadline       = itemView.findViewById(R.id.tvDeadline);
            tvTrustScore     = itemView.findViewById(R.id.tvTrustScore);
            tvVisit          = itemView.findViewById(R.id.tvVisit);
            tvTagFunding     = itemView.findViewById(R.id.tvTagFunding);
            tvTagEligibility = itemView.findViewById(R.id.tvTagEligibility);
            trustBar         = itemView.findViewById(R.id.trustBar);
        }
    }
}
