package com.jobato.api.service;

import com.jobato.api.dto.RunInput;
import com.jobato.api.dto.RunRequestedPayload;
import com.jobato.api.messaging.RunEventPublisher;
import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.model.QueryDefinition;
import com.jobato.api.repository.AllowlistRepository;
import com.jobato.api.repository.FileQueryRepository;
import com.jobato.api.repository.RunRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mockito;

import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class RunServiceTest {
    @TempDir
    Path tempDir;

    @Test
    void buildsRunRequestedPayloadWithInputs() {
        Path configDir = tempDir.resolve("config");
        FileQueryRepository queryRepository = new FileQueryRepository(configDir.toString());
        queryRepository.saveAll(List.of(
            new QueryDefinition("q-1", "Data Analyst", true, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z")
        ));

        AllowlistRepository allowlistRepository = new AllowlistRepository(configDir.resolve("allowlists.yaml").toString());
        allowlistRepository.saveAll(List.of(
            new AllowlistEntry("example.com", true)
        ));

        RunInputService runInputService = new RunInputService(queryRepository, allowlistRepository);
        RunRepository runRepository = Mockito.mock(RunRepository.class);
        RunEventPublisher runEventPublisher = Mockito.mock(RunEventPublisher.class);
        Clock clock = Clock.fixed(Instant.parse("2026-02-07T10:00:00Z"), ZoneOffset.UTC);
        RunService runService = new RunService(runInputService, runRepository, runEventPublisher, clock);

        RunRequestedPayload payload = runService.prepareRunRequestedPayload();

        assertThat(payload.runInputs()).hasSize(1);
        RunInput input = payload.runInputs().get(0);
        assertThat(input.queryId()).isEqualTo("q-1");
        assertThat(input.domain()).isEqualTo("example.com");
    }
}
