package com.jobato.api.dto;

import java.util.List;

public record RunRequestedPayload(List<RunInput> runInputs) {
}
