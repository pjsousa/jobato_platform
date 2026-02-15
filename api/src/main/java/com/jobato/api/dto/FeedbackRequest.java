package com.jobato.api.dto;

import jakarta.validation.constraints.NotNull;

public class FeedbackRequest {
    @NotNull
    private Integer resultId;

    private String label;

    public Integer getResultId() {
        return resultId;
    }

    public void setResultId(Integer resultId) {
        this.resultId = resultId;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }
}
