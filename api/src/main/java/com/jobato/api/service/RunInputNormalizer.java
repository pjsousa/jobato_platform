package com.jobato.api.service;

import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.model.QueryDefinition;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

final class RunInputNormalizer {
    private static final Pattern WHITESPACE = Pattern.compile("\\s+");

    private RunInputNormalizer() {
    }

    static List<QueryDefinition> normalizeEnabledQueries(List<QueryDefinition> queries) {
        if (queries == null || queries.isEmpty()) {
            return List.of();
        }

        Map<String, QueryDefinition> deduped = new LinkedHashMap<>();
        for (QueryDefinition query : queries) {
            if (query == null || !query.enabled()) {
                continue;
            }
            String canonicalText = canonicalizeQueryText(query.text());
            if (canonicalText.isBlank()) {
                throw new QueryValidationException("Query text is required");
            }
            String normalized = normalizeQueryText(canonicalText);
            deduped.computeIfAbsent(normalized, key -> new QueryDefinition(
                query.id(),
                canonicalText,
                true,
                query.createdAt(),
                query.updatedAt()
            ));
        }

        return List.copyOf(deduped.values());
    }

    static List<String> normalizeEnabledDomains(List<AllowlistEntry> entries) {
        if (entries == null || entries.isEmpty()) {
            return List.of();
        }

        Set<String> deduped = new LinkedHashSet<>();
        for (AllowlistEntry entry : entries) {
            if (entry == null || !entry.enabled()) {
                continue;
            }
            String normalized = AllowlistDomainNormalizer.normalize(entry.domain());
            deduped.add(normalized);
        }

        return List.copyOf(deduped);
    }

    private static String canonicalizeQueryText(String text) {
        if (text == null) {
            return "";
        }
        return WHITESPACE.matcher(text.trim()).replaceAll(" ");
    }

    private static String normalizeQueryText(String text) {
        return canonicalizeQueryText(text).toLowerCase(Locale.ROOT);
    }
}
