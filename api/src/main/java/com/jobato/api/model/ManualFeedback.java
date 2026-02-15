package com.jobato.api.model;

public class ManualFeedback {
    private final String manualLabel;
    private final String manualLabelUpdatedAt;

    public ManualFeedback(String manualLabel, String manualLabelUpdatedAt) {
        this.manualLabel = manualLabel;
        this.manualLabelUpdatedAt = manualLabelUpdatedAt;
    }

    public String getManualLabel() {
        return manualLabel;
    }

    public String getManualLabelUpdatedAt() {
        return manualLabelUpdatedAt;
    }
}
