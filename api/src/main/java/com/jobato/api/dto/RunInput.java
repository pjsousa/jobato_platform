package com.jobato.api.dto;

public record RunInput(
    String queryId,
    String queryText,
    String domain,
    String searchQuery
) {
}
