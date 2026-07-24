package com.inzira.app;

public class SearchRequest {
    public String query;
    public String category;
    public int max_results;
    public String district;

    public SearchRequest(String query, int max_results) {
        this.query = query;
        this.max_results = max_results;
    }

    public SearchRequest(String query, String category, int maxResults) {
        this(query, category, maxResults, null);
    }

    public SearchRequest(String query, String category, int maxResults, String district) {
        this.query = query;
        this.category = category;
        this.max_results = maxResults;
        this.district = district;
    }

    public static SearchRequest withDistrict(android.content.Context context, String query, String category, int max) {
        return new SearchRequest(query, category, max, InziraPrefs.getDistrict(context));
    }
}