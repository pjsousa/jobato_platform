package com.jobato.api.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class QuotaConfigRepositoryTest {
    @TempDir
    Path tempDir;

    @Test
    void loadsQuotaConfigFromFile() throws Exception {
        Path configFile = tempDir.resolve("quota.yaml");
        Files.writeString(configFile, """
            {
              \"quota\": {
                \"dailyLimit\": 100,
                \"concurrencyLimit\": 3,
                \"resetPolicy\": {
                  \"timeZone\": \"UTC\",
                  \"resetHour\": 0
                }
              }
            }
            """);

        QuotaConfigRepository repository = new QuotaConfigRepository(configFile.toString());
        QuotaSettings settings = repository.load();

        assertThat(settings.dailyLimit()).isEqualTo(100);
        assertThat(settings.concurrencyLimit()).isEqualTo(3);
        assertThat(settings.resetPolicy().timeZone()).isEqualTo("UTC");
        assertThat(settings.resetPolicy().resetHour()).isEqualTo(0);
    }
}
