package com.jobato.api.config;

public record QuotaResetPolicy(
    String timeZone,
    int resetHour
) {
}
