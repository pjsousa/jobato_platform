package com.jobato.api.dto;

public record QueryResponse(
    String id,
    String text,
    boolean enabled,
    String createdAt,
    String updatedAt
) {
}
