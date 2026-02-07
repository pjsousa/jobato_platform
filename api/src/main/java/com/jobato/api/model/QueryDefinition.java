package com.jobato.api.model;

public record QueryDefinition(
    String id,
    String text,
    boolean enabled,
    String createdAt,
    String updatedAt
) {
}
