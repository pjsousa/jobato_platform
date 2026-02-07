package com.jobato.api.dto;

import jakarta.validation.constraints.NotBlank;

public record QueryCreateRequest(
    @NotBlank String text
) {
}
