package com.jobato.api.dto;

public record QueryUpdateRequest(
    String text,
    Boolean enabled
) {
}
