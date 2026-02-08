package com.jobato.api.service;

import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.model.QueryDefinition;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class RunInputNormalizerTest {
    @Test
    void normalizesEnabledQueriesWithStableOrderingAndDedupe() {
        List<QueryDefinition> input = List.of(
            new QueryDefinition("1", "  Data   Analyst  ", true, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z"),
            new QueryDefinition("2", "data analyst", true, "2026-02-07T10:05:00Z", "2026-02-07T10:05:00Z"),
            new QueryDefinition("3", "Ignored", false, "2026-02-07T10:10:00Z", "2026-02-07T10:10:00Z"),
            new QueryDefinition("4", "UX   Researcher", true, "2026-02-07T10:15:00Z", "2026-02-07T10:15:00Z")
        );

        List<QueryDefinition> normalized = RunInputNormalizer.normalizeEnabledQueries(input);

        assertThat(normalized)
            .extracting(QueryDefinition::id)
            .containsExactly("1", "4");
        assertThat(normalized)
            .extracting(QueryDefinition::text)
            .containsExactly("Data Analyst", "UX Researcher");
    }

    @Test
    void normalizesEnabledDomainsWithStableOrderingAndDedupe() {
        List<AllowlistEntry> input = List.of(
            new AllowlistEntry(" Example.com. ", true),
            new AllowlistEntry("example.com", true),
            new AllowlistEntry("ignored.com", false),
            new AllowlistEntry("Other.com", true)
        );

        List<String> normalized = RunInputNormalizer.normalizeEnabledDomains(input);

        assertThat(normalized).containsExactly("example.com", "other.com");
    }
}
