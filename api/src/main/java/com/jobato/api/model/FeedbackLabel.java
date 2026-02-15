package com.jobato.api.model;

import java.util.Locale;

public enum FeedbackLabel {
    RELEVANT("relevant"),
    IRRELEVANT("irrelevant");

    private final String apiValue;

    FeedbackLabel(String apiValue) {
        this.apiValue = apiValue;
    }

    public String getApiValue() {
        return apiValue;
    }

    public static FeedbackLabel fromApiValue(String value) {
        if (value == null) {
            return null;
        }

        String normalized = value.trim().toLowerCase(Locale.ROOT);
        for (FeedbackLabel label : values()) {
            if (label.apiValue.equals(normalized)) {
                return label;
            }
        }

        throw new IllegalArgumentException("label must be one of: relevant, irrelevant, or null");
    }
}
