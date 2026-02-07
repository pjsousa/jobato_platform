package com.jobato.api.service;

import java.util.Locale;
import java.util.regex.Pattern;

public final class AllowlistDomainNormalizer {
    private static final Pattern DOMAIN_PATTERN = Pattern.compile(
            "^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
    );

    private AllowlistDomainNormalizer() {
    }

    public static String normalize(String input) {
        if (input == null) {
            throw new AllowlistDomainValidationException("Domain is required");
        }
        String trimmed = input.trim().toLowerCase(Locale.ROOT);
        if (trimmed.isEmpty()) {
            throw new AllowlistDomainValidationException("Domain is required");
        }
        if (trimmed.endsWith(".")) {
            trimmed = trimmed.substring(0, trimmed.length() - 1);
        }
        if (trimmed.contains("://") || trimmed.contains("/") || trimmed.contains("\\") || trimmed.contains(":") || trimmed.contains("*")) {
            throw new AllowlistDomainValidationException("Domain must not include scheme, path, port, or wildcard");
        }
        if (trimmed.length() > 253) {
            throw new AllowlistDomainValidationException("Domain is too long");
        }
        if (!DOMAIN_PATTERN.matcher(trimmed).matches()) {
            throw new AllowlistDomainValidationException("Domain format is invalid");
        }
        return trimmed;
    }
}
