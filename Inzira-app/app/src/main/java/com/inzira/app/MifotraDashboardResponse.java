package com.inzira.app;

import java.util.List;

public class MifotraDashboardResponse {
    public int days;
    public RegistrySection registry;
    public YouthAnalyticsSection youth_analytics;

    public static class RegistrySection {
        public int verified_total;
        public int new_verified;
        public int new_domains_detected;
        public int pending_verification;
        public java.util.Map<String, Integer> verified_by_tld;
        public java.util.Map<String, Integer> by_category;
        public String last_refresh_at;
        public List<OpportunityResult> new_websites;
        public List<OpportunityResult> all_websites;
    }

    public static class YouthAnalyticsSection {
        public AnalyticsSummary summary;
        public List<CategoryStat> top_categories;
        public List<ZeroResultQuery> zero_result_queries;
        public List<DistrictStat> top_districts;
    }

    public static class AnalyticsSummary {
        public int days;
        public int total_searches;
        public int zero_result_searches;
        public int unique_districts;
        public float zero_result_rate_pct;
    }

    public static class CategoryStat {
        public String category;
        public int searches;
    }

    public static class ZeroResultQuery {
        public String query;
        public String category;
        public String district;
        public int times_searched;
        public String last_searched;
    }

    public static class DistrictStat {
        public String district;
        public int searches;
        public int zero_result_searches;
    }
}
