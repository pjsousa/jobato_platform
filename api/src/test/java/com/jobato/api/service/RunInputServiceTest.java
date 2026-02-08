package com.jobato.api.service;

import com.jobato.api.dto.RunInput;
import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.model.QueryDefinition;
import com.jobato.api.repository.AllowlistRepository;
import com.jobato.api.repository.FileQueryRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RunInputServiceTest {
    @TempDir
    Path tempDir;

    @Test
    void buildsRunInputsWithSearchQuery() {
        RunInputService service = createService(
            List.of(new QueryDefinition("q-1", "Data Analyst", true, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z")),
            List.of(new AllowlistEntry("example.com", true))
        );

        List<RunInput> inputs = service.buildRunInputs();

        assertThat(inputs).hasSize(1);
        RunInput input = inputs.get(0);
        assertThat(input.queryId()).isEqualTo("q-1");
        assertThat(input.queryText()).isEqualTo("Data Analyst");
        assertThat(input.domain()).isEqualTo("example.com");
        assertThat(input.searchQuery()).isEqualTo("site:example.com Data Analyst");
    }

    @Test
    void filtersDisabledEntriesAndBuildsInQueryThenDomainOrder() {
        RunInputService service = createService(
            List.of(
                new QueryDefinition("q-1", "Data Analyst", true, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z"),
                new QueryDefinition("q-2", "Product Manager", false, "2026-02-07T10:05:00Z", "2026-02-07T10:05:00Z"),
                new QueryDefinition("q-3", "UX Researcher", true, "2026-02-07T10:10:00Z", "2026-02-07T10:10:00Z")
            ),
            List.of(
                new AllowlistEntry("example.com", true),
                new AllowlistEntry("ignored.com", false),
                new AllowlistEntry("careers.com", true)
            )
        );

        List<RunInput> inputs = service.buildRunInputs();

        assertThat(inputs)
            .extracting(RunInput::searchQuery)
            .containsExactly(
                "site:example.com Data Analyst",
                "site:careers.com Data Analyst",
                "site:example.com UX Researcher",
                "site:careers.com UX Researcher"
            );
    }

    @Test
    void dedupesQueriesAndDomainsAfterNormalization() {
        RunInputService service = createService(
            List.of(
                new QueryDefinition("q-1", "Data Analyst", true, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z"),
                new QueryDefinition("q-2", " data   analyst ", true, "2026-02-07T10:05:00Z", "2026-02-07T10:05:00Z"),
                new QueryDefinition("q-3", "Product Manager", true, "2026-02-07T10:10:00Z", "2026-02-07T10:10:00Z")
            ),
            List.of(
                new AllowlistEntry("Example.com.", true),
                new AllowlistEntry("example.com", true),
                new AllowlistEntry("careers.com", true)
            )
        );

        List<RunInput> inputs = service.buildRunInputs();

        assertThat(inputs).hasSize(4);
        assertThat(inputs).extracting(RunInput::queryId).doesNotContain("q-2");
        assertThat(inputs)
            .extracting(RunInput::searchQuery)
            .containsExactly(
                "site:example.com Data Analyst",
                "site:careers.com Data Analyst",
                "site:example.com Product Manager",
                "site:careers.com Product Manager"
            );
    }

    @Test
    void throwsWhenNoEnabledInputs() {
        RunInputService service = createService(
            List.of(new QueryDefinition("q-1", "Data Analyst", false, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z")),
            List.of(new AllowlistEntry("example.com", true))
        );

        assertThatThrownBy(service::buildRunInputs)
            .isInstanceOf(NoEnabledInputsException.class)
            .hasMessageContaining("Add or enable queries and domains");
    }

    private RunInputService createService(List<QueryDefinition> queries, List<AllowlistEntry> allowlists) {
        Path configDir = tempDir.resolve("config-" + System.nanoTime());
        FileQueryRepository queryRepository = new FileQueryRepository(configDir.toString());
        queryRepository.saveAll(queries);

        AllowlistRepository allowlistRepository = new AllowlistRepository(configDir.resolve("allowlists.yaml").toString());
        allowlistRepository.saveAll(allowlists);

        return new RunInputService(queryRepository, allowlistRepository);
    }
}
