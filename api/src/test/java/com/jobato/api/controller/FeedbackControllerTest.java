package com.jobato.api.controller;

import com.jobato.api.model.ManualFeedback;
import com.jobato.api.service.FeedbackNotFoundException;
import com.jobato.api.service.FeedbackService;
import com.jobato.api.service.FeedbackValidationException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = FeedbackController.class)
@Import(ApiExceptionHandler.class)
class FeedbackControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private FeedbackService feedbackService;

    @Test
    void postFeedback_acceptsRelevantLabel() throws Exception {
        when(feedbackService.setManualLabel(10, "relevant"))
            .thenReturn(new ManualFeedback("relevant", "2026-02-15T12:00:00Z"));

        mockMvc.perform(post("/api/feedback")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"resultId\":10,\"label\":\"relevant\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.resultId").value(10))
            .andExpect(jsonPath("$.manualLabel").value("relevant"))
            .andExpect(jsonPath("$.manualLabelUpdatedAt").value("2026-02-15T12:00:00Z"));
    }

    @Test
    void postFeedback_acceptsIrrelevantLabel() throws Exception {
        when(feedbackService.setManualLabel(11, "irrelevant"))
            .thenReturn(new ManualFeedback("irrelevant", "2026-02-15T12:00:00Z"));

        mockMvc.perform(post("/api/feedback")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"resultId\":11,\"label\":\"irrelevant\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.manualLabel").value("irrelevant"));
    }

    @Test
    void postFeedback_acceptsNullLabelForClear() throws Exception {
        when(feedbackService.setManualLabel(12, null))
            .thenReturn(new ManualFeedback(null, "2026-02-15T12:00:00Z"));

        mockMvc.perform(post("/api/feedback")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"resultId\":12,\"label\":null}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.resultId").value(12))
            .andExpect(jsonPath("$.manualLabel").doesNotExist())
            .andExpect(jsonPath("$.manualLabelUpdatedAt").value("2026-02-15T12:00:00Z"));
    }

    @Test
    void postFeedback_rejectsInvalidLabelWithRfc7807Payload() throws Exception {
        when(feedbackService.setManualLabel(13, "bad"))
            .thenThrow(new FeedbackValidationException("label must be one of: relevant, irrelevant, or null"));

        mockMvc.perform(post("/api/feedback")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"resultId\":13,\"label\":\"bad\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.title").value("Validation error"))
            .andExpect(jsonPath("$.detail").value("label must be one of: relevant, irrelevant, or null"))
            .andExpect(jsonPath("$.type").value("https://jobato/errors/validation"))
            .andExpect(jsonPath("$.status").value(400));
    }

    @Test
    void postFeedback_returnsNotFoundForUnknownResult() throws Exception {
        when(feedbackService.setManualLabel(404, "relevant"))
            .thenThrow(new FeedbackNotFoundException("Result not found: 404"));

        mockMvc.perform(post("/api/feedback")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"resultId\":404,\"label\":\"relevant\"}"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.title").value("Not found"))
            .andExpect(jsonPath("$.detail").value("Result not found: 404"))
            .andExpect(jsonPath("$.type").value("https://jobato/errors/not-found"))
            .andExpect(jsonPath("$.status").value(404));
    }

    @Test
    void postFeedback_requiresResultId() throws Exception {
        mockMvc.perform(post("/api/feedback")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"label\":\"relevant\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.title").value("Validation error"))
            .andExpect(jsonPath("$.type").value("https://jobato/errors/validation"));
    }
}
