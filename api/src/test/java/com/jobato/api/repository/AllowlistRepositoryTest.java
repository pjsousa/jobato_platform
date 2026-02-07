package com.jobato.api.repository;

import com.jobato.api.model.AllowlistEntry;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class AllowlistRepositoryTest {
    @TempDir
    Path tempDir;

    @Test
    void findAllReturnsEmptyWhenFileMissing() {
        AllowlistRepository repository = new AllowlistRepository(tempDir.resolve("allowlists.yaml"));

        assertThat(repository.findAll()).isEmpty();
    }

    @Test
    void saveAllWritesAndReadsEntries() {
        AllowlistRepository repository = new AllowlistRepository(tempDir.resolve("allowlists.yaml"));

        List<AllowlistEntry> entries = List.of(
                new AllowlistEntry("example.com", true),
                new AllowlistEntry("jobs.example.com", false)
        );

        repository.saveAll(entries);

        assertThat(repository.findAll()).containsExactlyElementsOf(entries);
    }
}
