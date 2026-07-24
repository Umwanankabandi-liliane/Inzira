package com.inzira.app;

public class ChatMessage {
    public final String text;
    public final boolean isUser;

    public ChatMessage(String text, boolean isUser) {
        this.text = text;
        this.isUser = isUser;
    }
}
