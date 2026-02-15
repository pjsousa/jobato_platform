package com.jobato.api.controller;

import com.jobato.api.dto.FeedbackRequest;
import com.jobato.api.dto.FeedbackResponse;
import com.jobato.api.model.ManualFeedback;
import com.jobato.api.service.FeedbackService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/feedback")
public class FeedbackController {
    private final FeedbackService feedbackService;

    public FeedbackController(FeedbackService feedbackService) {
        this.feedbackService = feedbackService;
    }

    @PostMapping
    public ResponseEntity<FeedbackResponse> setFeedback(@Valid @RequestBody FeedbackRequest request) {
        ManualFeedback feedback = feedbackService.setManualLabel(request.getResultId(), request.getLabel());
        FeedbackResponse response = new FeedbackResponse(
            request.getResultId(),
            feedback.getManualLabel(),
            feedback.getManualLabelUpdatedAt()
        );
        return ResponseEntity.ok(response);
    }
}
