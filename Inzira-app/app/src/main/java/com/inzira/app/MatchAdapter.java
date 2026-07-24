package com.inzira.app;

import android.content.Intent;
import android.net.Uri;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class MatchAdapter extends RecyclerView.Adapter<MatchAdapter.ViewHolder> {

    private final List<OpportunityResult> results;
    private final android.content.Context context;

    public MatchAdapter(List<OpportunityResult> results, android.content.Context context) {
        this.results = results;
        this.context = context;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_match, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        OpportunityResult result = results.get(position);
        holder.tvTitle.setText(WebsiteDisplayHelper.opportunityTitle(result));
        holder.tvCategory.setText(WebsiteDisplayHelper.categoryLabel(result.category));
        holder.tvMatchLabel.setText(LanguageHelper.matchFitLabel(context));
        holder.tvWhyFitTitle.setText(LanguageHelper.whyYouFit(context));
        holder.tvTrustScore.setText((InziraPrefs.isKinyarwanda(context) ? "Icyizere " : "Trust ")
                + WebsiteDisplayHelper.trustDecimal(result.trust_score));

        int matchScore = result.match_score > 0 ? result.match_score : 0;
        holder.tvMatchScore.setText(matchScore + "%");
        holder.matchBar.setProgress(matchScore);
        holder.tvMatchTier.setText(LanguageHelper.matchTier(context, matchScore));
        holder.tvMatchTier.setTextColor(matchTierColor(matchScore));

        int scoreBg = matchScore >= 80 ? R.color.success_green
                : matchScore >= 65 ? R.color.medium_blue
                : matchScore >= 50 ? R.color.primary_dark_blue
                : R.color.text_muted;
        holder.tvMatchScore.setBackgroundTintList(
                android.content.res.ColorStateList.valueOf(ContextCompat.getColor(context, scoreBg)));

        String competition = LanguageHelper.competitionLabel(context, result.competition);
        if (competition != null && !competition.isEmpty()) {
            holder.tvCompetition.setText(competition);
            holder.tvCompetition.setVisibility(View.VISIBLE);
        } else {
            holder.tvCompetition.setVisibility(View.GONE);
        }

        holder.tvUrl.setText(WebsiteDisplayHelper.opportunityEmployer(result));

        if (result.match_reasons != null && !result.match_reasons.isEmpty()) {
            StringBuilder why = new StringBuilder();
            for (String reason : result.match_reasons) {
                why.append("• ").append(reason).append("\n");
            }
            holder.tvWhyFit.setText(why.toString().trim());
            holder.tvWhyFitTitle.setVisibility(View.VISIBLE);
            holder.tvWhyFit.setVisibility(View.VISIBLE);
        } else {
            holder.tvWhyFitTitle.setVisibility(View.GONE);
            holder.tvWhyFit.setVisibility(View.GONE);
        }

        holder.cardView.setOnClickListener(v -> openDetail(result));
        holder.btnVisit.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(WebsiteDisplayHelper.applyUrl(result)));
            context.startActivity(intent);
        });
        holder.btnVisit.setText(InziraPrefs.isKinyarwanda(context) ? "Saba" : "Apply");
    }

    private int matchTierColor(int score) {
        if (score >= 80) {
            return ContextCompat.getColor(context, R.color.success_green);
        }
        if (score >= 65) {
            return ContextCompat.getColor(context, R.color.medium_blue);
        }
        if (score >= 50) {
            return ContextCompat.getColor(context, R.color.primary_dark_blue);
        }
        return ContextCompat.getColor(context, R.color.text_muted);
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
        View cardView;
        TextView tvTitle, tvUrl, tvCategory, tvTrustScore, tvMatchScore, tvMatchLabel;
        TextView tvWhyFit, tvWhyFitTitle, tvMatchTier, tvCompetition, btnVisit;
        ProgressBar matchBar;

        ViewHolder(View itemView) {
            super(itemView);
            cardView = itemView.findViewById(R.id.cardView);
            tvTitle = itemView.findViewById(R.id.tvTitle);
            tvUrl = itemView.findViewById(R.id.tvUrl);
            tvCategory = itemView.findViewById(R.id.tvCategory);
            tvTrustScore = itemView.findViewById(R.id.tvTrustScore);
            tvMatchScore = itemView.findViewById(R.id.tvMatchScore);
            tvMatchLabel = itemView.findViewById(R.id.tvMatchLabel);
            tvWhyFit = itemView.findViewById(R.id.tvWhyFit);
            tvWhyFitTitle = itemView.findViewById(R.id.tvWhyFitTitle);
            tvMatchTier = itemView.findViewById(R.id.tvMatchTier);
            tvCompetition = itemView.findViewById(R.id.tvCompetition);
            btnVisit = itemView.findViewById(R.id.btnVisit);
            matchBar = itemView.findViewById(R.id.matchBar);
        }
    }
}
