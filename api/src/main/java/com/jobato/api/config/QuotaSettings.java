package com.jobato.api.config;

public record QuotaSettings(
    int dailyLimit,
    int concurrencyLimit,
    QuotaResetPolicy resetPolicy
) {
}
