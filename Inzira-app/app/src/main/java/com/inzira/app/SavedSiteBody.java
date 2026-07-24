package com.inzira.app;

public class SavedSiteBody {
    public String url;
    public String title;
    public String category;
    public Boolean notify_enabled;

    public SavedSiteBody(String url, String title, String category, Boolean notifyEnabled) {
        this.url = url;
        this.title = title;
        this.category = category;
        this.notify_enabled = notifyEnabled;
    }
}
