package com.jobato.api.repository;

import com.jobato.api.model.QueryDefinition;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.io.StringWriter;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
public class FileQueryRepository implements QueryRepository {
    private final Path queriesPath;
    private final Yaml yaml;

    public FileQueryRepository(@Value("${CONFIG_DIR:config}") String configDir) {
        this.queriesPath = Paths.get(configDir).resolve("queries.yaml");
        this.yaml = new Yaml();
    }

    @Override
    public synchronized List<QueryDefinition> loadAll() {
        return List.copyOf(readAll());
    }

    @Override
    public synchronized void saveAll(List<QueryDefinition> queries) {
        writeAll(queries);
    }

    private List<QueryDefinition> readAll() {
        if (!Files.exists(queriesPath)) {
            return List.of();
        }

        String content;
        try {
            content = Files.readString(queriesPath, StandardCharsets.UTF_8);
        } catch (IOException exception) {
            throw new UncheckedIOException(exception);
        }

        if (content.isBlank()) {
            return List.of();
        }

        Object loaded = yaml.load(content);
        if (loaded == null) {
            return List.of();
        }

        if (!(loaded instanceof Map<?, ?> root)) {
            throw new IllegalStateException("Invalid queries.yaml format: expected a map at root");
        }

        Object queriesNode = root.get("queries");
        if (queriesNode == null) {
            return List.of();
        }

        if (!(queriesNode instanceof List<?> rawQueries)) {
            throw new IllegalStateException("Invalid queries.yaml format: queries must be a list");
        }

        List<QueryDefinition> queries = new ArrayList<>();
        for (Object rawQuery : rawQueries) {
            if (!(rawQuery instanceof Map<?, ?> queryMap)) {
                throw new IllegalStateException("Invalid queries.yaml format: query entry must be a map");
            }
            queries.add(parseQuery(queryMap));
        }
        return queries;
    }

    private QueryDefinition parseQuery(Map<?, ?> queryMap) {
        String id = readString(queryMap, "id");
        String text = readString(queryMap, "text");
        Boolean enabled = readBoolean(queryMap, "enabled");
        String createdAt = readString(queryMap, "createdAt");
        String updatedAt = readString(queryMap, "updatedAt");

        if (id.isBlank() || text.isBlank() || createdAt.isBlank() || updatedAt.isBlank()) {
            throw new IllegalStateException("Invalid queries.yaml format: query fields cannot be blank");
        }

        return new QueryDefinition(id, text, enabled, createdAt, updatedAt);
    }

    private String readString(Map<?, ?> queryMap, String key) {
        Object value = queryMap.get(key);
        if (!(value instanceof String textValue)) {
            throw new IllegalStateException("Invalid queries.yaml format: " + key + " must be a string");
        }
        return textValue;
    }

    private Boolean readBoolean(Map<?, ?> queryMap, String key) {
        Object value = queryMap.get(key);
        if (!(value instanceof Boolean booleanValue)) {
            throw new IllegalStateException("Invalid queries.yaml format: " + key + " must be a boolean");
        }
        return booleanValue;
    }

    private void writeAll(List<QueryDefinition> queries) {
        try {
            Files.createDirectories(queriesPath.getParent());
        } catch (IOException exception) {
            throw new UncheckedIOException(exception);
        }

        List<Map<String, Object>> queryItems = new ArrayList<>();
        for (QueryDefinition query : queries) {
            Map<String, Object> queryMap = new LinkedHashMap<>();
            queryMap.put("id", query.id());
            queryMap.put("text", query.text());
            queryMap.put("enabled", query.enabled());
            queryMap.put("createdAt", query.createdAt());
            queryMap.put("updatedAt", query.updatedAt());
            queryItems.add(queryMap);
        }

        Map<String, Object> root = new LinkedHashMap<>();
        root.put("queries", queryItems);

        StringWriter writer = new StringWriter();
        yaml.dump(root, writer);
        atomicWrite(writer.toString());
    }

    private void atomicWrite(String content) {
        Path tempPath;
        try {
            tempPath = Files.createTempFile(queriesPath.getParent(), "queries", ".yaml.tmp");
            Files.writeString(tempPath, content, StandardCharsets.UTF_8, StandardOpenOption.TRUNCATE_EXISTING);
        } catch (IOException exception) {
            throw new UncheckedIOException(exception);
        }

        try {
            Files.move(tempPath, queriesPath, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException exception) {
            try {
                Files.move(tempPath, queriesPath, StandardCopyOption.REPLACE_EXISTING);
            } catch (IOException fallbackException) {
                throw new UncheckedIOException(fallbackException);
            }
        } catch (IOException exception) {
            throw new UncheckedIOException(exception);
        }
    }
}
