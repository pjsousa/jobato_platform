package com.jobato.api.service;

import com.jobato.api.model.QueryDefinition;
import com.jobato.api.repository.QueryRepository;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Pattern;

@Service
public class QueryService {
    private static final Pattern WHITESPACE = Pattern.compile("\\s+");
    private static final DateTimeFormatter TIMESTAMP_FORMAT = DateTimeFormatter.ISO_OFFSET_DATE_TIME;

    private final QueryRepository repository;
    private final Clock clock;
    private final Object lock = new Object();

    public QueryService(QueryRepository repository, Clock clock) {
        this.repository = repository;
        this.clock = clock;
    }

    public List<QueryDefinition> list() {
        return List.copyOf(repository.loadAll());
    }

    public QueryDefinition create(String text) {
        String canonicalText = canonicalize(text);
        if (canonicalText.isBlank()) {
            throw new QueryValidationException("Query text is required");
        }

        synchronized (lock) {
            List<QueryDefinition> existing = repository.loadAll();
            assertNoDuplicate(existing, canonicalText, null);

            String now = timestamp();
            QueryDefinition created = new QueryDefinition(
                UUID.randomUUID().toString(),
                canonicalText,
                true,
                now,
                now
            );

            List<QueryDefinition> updated = new ArrayList<>(existing);
            updated.add(created);
            repository.saveAll(updated);
            return created;
        }
    }

    public QueryDefinition update(String id, String text, Boolean enabled) {
        if (id == null || id.isBlank()) {
            throw new QueryValidationException("Query id is required");
        }

        synchronized (lock) {
            List<QueryDefinition> existing = repository.loadAll();
            QueryDefinition current = existing.stream()
                .filter(query -> query.id().equals(id))
                .findFirst()
                .orElseThrow(() -> new QueryNotFoundException("Query not found"));

            String updatedText = current.text();
            if (text != null) {
                String canonicalText = canonicalize(text);
                if (canonicalText.isBlank()) {
                    throw new QueryValidationException("Query text is required");
                }
                assertNoDuplicate(existing, canonicalText, current.id());
                updatedText = canonicalText;
            }

            boolean updatedEnabled = enabled != null ? enabled : current.enabled();
            if (text == null && enabled == null) {
                throw new QueryValidationException("At least one field must be provided to update");
            }

            QueryDefinition updated = new QueryDefinition(
                current.id(),
                updatedText,
                updatedEnabled,
                current.createdAt(),
                timestamp()
            );

            List<QueryDefinition> updatedQueries = new ArrayList<>(existing.size());
            for (QueryDefinition query : existing) {
                updatedQueries.add(query.id().equals(current.id()) ? updated : query);
            }
            repository.saveAll(updatedQueries);
            return updated;
        }
    }

    private void assertNoDuplicate(List<QueryDefinition> existing, String candidateText, String currentId) {
        String normalized = normalize(candidateText);
        for (QueryDefinition query : existing) {
            if (currentId != null && query.id().equals(currentId)) {
                continue;
            }
            if (normalize(query.text()).equals(normalized)) {
                throw new QueryValidationException("Duplicate query text is not allowed");
            }
        }
    }

    private String canonicalize(String text) {
        if (text == null) {
            return "";
        }
        return WHITESPACE.matcher(text.trim()).replaceAll(" ");
    }

    private String normalize(String text) {
        return canonicalize(text).toLowerCase(Locale.ROOT);
    }

    private String timestamp() {
        return OffsetDateTime.now(clock).withOffsetSameInstant(ZoneOffset.UTC).format(TIMESTAMP_FORMAT);
    }
}
