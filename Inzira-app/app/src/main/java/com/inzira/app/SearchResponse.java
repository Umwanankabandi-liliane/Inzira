package com.inzira.app;

import java.util.List;

public class SearchResponse {
    public String query;
    public int total_found;
    public int verified;
    public List<OpportunityResult> results;
}