package com.inzira.app;

public class AssistantRequest {
    public String message;
    public String language;

    public AssistantRequest(String message, String language) {
        this.message = message;
        this.language = language;
    }
}