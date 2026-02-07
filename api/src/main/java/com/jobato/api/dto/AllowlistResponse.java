package com.jobato.api.dto;

import com.jobato.api.model.AllowlistEntry;

public record AllowlistResponse(String domain, boolean enabled) {
    public static AllowlistResponse fromEntry(AllowlistEntry entry) {
        return new AllowlistResponse(entry.domain(), entry.enabled());
    }
}
