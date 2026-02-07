package com.jobato.api.service;

import com.jobato.api.model.QueryDefinition;
import com.jobato.api.repository.FileQueryRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class QueryServiceTest {
    @TempDir
    Path tempDir;

    @Test
    void createsQueryWithDefaultsAndNormalization() {
        MutableClock clock = new MutableClock(Instant.parse("2026-02-07T10:00:00Z"));
        QueryService service = createService(clock);

        QueryDefinition created = service.create("  Data   Analyst  ");

        assertThat(created.enabled()).isTrue();
        assertThat(created.text()).isEqualTo("Data Analyst");
        assertThat(created.createdAt()).isEqualTo("2026-02-07T10:00:00Z");
        assertThat(created.updatedAt()).isEqualTo("2026-02-07T10:00:00Z");
        assertThat(service.list()).hasSize(1);
    }

    @Test
    void rejectsDuplicatesIgnoringCaseAndWhitespace() {
        MutableClock clock = new MutableClock(Instant.parse("2026-02-07T10:00:00Z"));
        QueryService service = createService(clock);

        service.create("Data Analyst");

        assertThatThrownBy(() -> service.create(" data   ANALYST "))
            .isInstanceOf(QueryValidationException.class)
            .hasMessageContaining("Duplicate query");
    }

    @Test
    void updateKeepsCreatedAtAndUpdatesUpdatedAt() {
        MutableClock clock = new MutableClock(Instant.parse("2026-02-07T10:00:00Z"));
        QueryService service = createService(clock);

        QueryDefinition created = service.create("Data Analyst");
        clock.setInstant(Instant.parse("2026-02-07T11:00:00Z"));

        QueryDefinition updated = service.update(created.id(), "  Senior   Analyst  ", null);

        assertThat(updated.createdAt()).isEqualTo(created.createdAt());
        assertThat(updated.updatedAt()).isEqualTo("2026-02-07T11:00:00Z");
        assertThat(updated.text()).isEqualTo("Senior Analyst");
    }

    @Test
    void disableKeepsRecord() {
        MutableClock clock = new MutableClock(Instant.parse("2026-02-07T10:00:00Z"));
        QueryService service = createService(clock);

        QueryDefinition created = service.create("UX Researcher");
        clock.setInstant(Instant.parse("2026-02-07T12:00:00Z"));

        QueryDefinition disabled = service.update(created.id(), null, false);

        assertThat(disabled.enabled()).isFalse();
        assertThat(disabled.text()).isEqualTo("UX Researcher");
        assertThat(service.list()).hasSize(1);
    }

    private QueryService createService(MutableClock clock) {
        Path configDir = tempDir.resolve("config");
        FileQueryRepository repository = new FileQueryRepository(configDir.toString());
        return new QueryService(repository, clock);
    }

    private static final class MutableClock extends Clock {
        private Instant instant;

        private MutableClock(Instant instant) {
            this.instant = instant;
        }

        void setInstant(Instant instant) {
            this.instant = instant;
        }

        @Override
        public ZoneId getZone() {
            return ZoneId.of("UTC");
        }

        @Override
        public Clock withZone(ZoneId zone) {
            return this;
        }

        @Override
        public Instant instant() {
            return instant;
        }
    }
}
