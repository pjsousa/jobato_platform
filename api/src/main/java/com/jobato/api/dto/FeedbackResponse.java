package com.jobato.api.dto;

public class FeedbackResponse {
    private final Integer resultId;
    private final String manualLabel;
    private final String manualLabelUpdatedAt;

    public FeedbackResponse(Integer resultId, String manualLabel, String manualLabelUpdatedAt) {
        this.resultId = resultId;
        this.manualLabel = manualLabel;
        this.manualLabelUpdatedAt = manualLabelUpdatedAt;
    }

    public Integer getResultId() {
        return resultId;
    }

    public String getManualLabel() {
        return manualLabel;
    }

    public String getManualLabelUpdatedAt() {
        return manualLabelUpdatedAt;
    }
}
