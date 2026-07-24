package com.inzira.app;

import java.util.List;
import java.util.stream.Collectors;

public final class WebsiteDisplayHelper {

    private WebsiteDisplayHelper() {
    }

    public static String websiteName(OpportunityResult result) {
        return opportunityTitle(result);
    }

    public static String opportunityTitle(OpportunityResult result) {
        if (result == null) {
            return "Opportunity";
        }
        String title = result.title != null ? result.title.trim() : "";
        String org = result.organization != null ? result.organization.trim() : "";
        String cat = categoryLabel(result.category);
        if (!title.isEmpty() && title.length() > 4 && !title.toLowerCase().startsWith("http")) {
            return title.length() > 72 ? title.substring(0, 69) + "…" : title;
        }
        if (!org.isEmpty()) {
            return cat + " — " + org;
        }
        if (result.domain != null && !result.domain.isEmpty()) {
            return cat + " — " + result.domain;
        }
        return cat;
    }

    public static String opportunityEmployer(OpportunityResult result) {
        if (result == null) {
            return "";
        }
        if (result.organization != null && !result.organization.trim().isEmpty()) {
            return result.organization.trim();
        }
        if (result.location != null && !result.location.trim().isEmpty()) {
            return result.location.trim();
        }
        if (result.domain != null && !result.domain.trim().isEmpty()) {
            return result.domain.trim();
        }
        try {
            android.net.Uri uri = android.net.Uri.parse(result.url);
            return uri.getHost() != null ? uri.getHost() : "";
        } catch (Exception e) {
            return "";
        }
    }

    public static String applyUrl(OpportunityResult result) {
        if (result == null) {
            return "";
        }
        if (result.apply_link != null && !result.apply_link.trim().isEmpty()) {
            return result.apply_link.trim();
        }
        return result.url != null ? result.url.trim() : "";
    }

    public static String hostsLine(OpportunityResult result) {
        if (result.categories != null && !result.categories.isEmpty()) {
            return "Hosts: " + result.categories.stream()
                    .map(WebsiteDisplayHelper::labelForCategory)
                    .collect(Collectors.joining(" · "));
        }
        if (result.category != null && !result.category.isEmpty()) {
            return "Hosts: " + labelForCategory(result.category);
        }
        return "Hosts opportunities in Rwanda";
    }

    public static String trustLabel(int trust) {
        return trust + "% verified";
    }

    public static String trustDecimal(float score) {
        float normalized = score > 1f ? score / 100f : score;
        return String.format(java.util.Locale.US, "%.2f", normalized);
    }

    public static int trustPercent(float score) {
        if (score <= 1f) {
            return Math.round(score * 100f);
        }
        return Math.round(score);
    }

    public static String categoryLabel(String category) {
        if (category == null || category.trim().isEmpty()) {
            return "General";
        }
        String key = category.trim().toLowerCase();
        switch (key) {
            case "scholarship": return "Scholarship";
            case "job":         return "Job";
            case "internship":  return "Internship";
            case "training":    return "Training";
            case "program":     return "Program";
            case "free_course": return "Free course";
            case "competition": return "Competition";
            default:
                String spaced = key.replace("_", " ");
                return spaced.substring(0, 1).toUpperCase() + spaced.substring(1);
        }
    }

    public static String fundingTag(OpportunityResult result) {
        String text = ((result.snippet != null ? result.snippet : "") + " "
                + (result.eligibility != null ? result.eligibility : "")).toLowerCase();
        if (text.contains("full tuition") || text.contains("full funding") || text.contains("full scholarship")) {
            return "Full funding";
        }
        if (text.contains("partial") || text.contains("stipend")) {
            return "Partial funding";
        }
        if ("scholarship".equalsIgnoreCase(result.category)) {
            return "Scholarship";
        }
        return null;
    }

    public static String eligibilityTag(OpportunityResult result) {
        if (result.eligibility != null && !result.eligibility.trim().isEmpty()) {
            String e = result.eligibility.trim();
            if (e.length() > 24) {
                return e.substring(0, 21) + "...";
            }
            return e;
        }
        if (result.location != null && result.location.toLowerCase().contains("government")) {
            return "Government";
        }
        return null;
    }

    public static String deadlineLabel(OpportunityResult result) {
        if (result.deadline != null && !result.deadline.trim().isEmpty()) {
            String d = result.deadline.trim();
            if (d.toLowerCase().startsWith("deadline")) {
                return d;
            }
            return "Deadline: " + d;
        }
        return "Deadline: Check website";
    }

    public static String aiSummary(OpportunityResult result) {
        if (result.snippet != null && !result.snippet.trim().isEmpty()) {
            return result.snippet.trim();
        }
        return "Inzira AI verified this listing from a trusted Rwanda opportunity source. "
                + "Apply on the official portal for full eligibility and steps.";
    }

    public static String benefitLine(OpportunityResult result) {
        String snippet = result.snippet != null ? result.snippet.trim() : "";
        if (!snippet.isEmpty()) {
            int end = snippet.indexOf('.');
            if (end > 0 && end < 80) {
                return snippet.substring(0, end + 1);
            }
            if (snippet.length() > 80) {
                return snippet.substring(0, 77) + "...";
            }
            return snippet;
        }
        return "See website for full benefit details";
    }

    private static String labelForCategory(String category) {
        switch (category) {
            case "scholarship": return "scholarships";
            case "job":         return "jobs";
            case "internship":  return "internships";
            case "training":    return "training";
            case "competition": return "competitions";
            case "program":     return "programs";
            case "free_course": return "free courses";
            default:            return category.replace("_", " ");
        }
    }
}
