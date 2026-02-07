package com.jobato.api.repository;

import com.jobato.api.model.AllowlistEntry;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
public class AllowlistRepository {
    private static final String ROOT_KEY = "allowlists";

    private final Path filePath;
    private final Yaml yaml;

    @Autowired
    public AllowlistRepository(@Value("${allowlist.file-path:config/allowlists.yaml}") String filePath) {
        this(Path.of(filePath));
    }

    AllowlistRepository(Path filePath) {
        this.filePath = filePath;
        this.yaml = new Yaml(buildDumperOptions());
    }

    public List<AllowlistEntry> findAll() {
        if (!Files.exists(filePath)) {
            return List.of();
        }

        try (InputStream inputStream = Files.newInputStream(filePath)) {
            Object loaded = yaml.load(inputStream);
            if (!(loaded instanceof Map<?, ?> root)) {
                return List.of();
            }
            Object entries = root.get(ROOT_KEY);
            if (!(entries instanceof List<?> list)) {
                return List.of();
            }
            List<AllowlistEntry> results = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof Map<?, ?> map) {
                    AllowlistEntry entry = fromMap(map);
                    if (entry != null) {
                        results.add(entry);
                    }
                }
            }
            return results;
        } catch (IOException exception) {
            throw new UncheckedIOException("Failed to read allowlist file", exception);
        }
    }

    public void saveAll(List<AllowlistEntry> entries) {
        Map<String, Object> root = new LinkedHashMap<>();
        List<Map<String, Object>> values = new ArrayList<>();
        for (AllowlistEntry entry : entries) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("domain", entry.domain());
            item.put("enabled", entry.enabled());
            values.add(item);
        }
        root.put(ROOT_KEY, values);

        String output = yaml.dump(root);
        writeAtomically(output);
    }

    private void writeAtomically(String output) {
        try {
            Path parent = filePath.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Path tempFile = Files.createTempFile(parent, "allowlists-", ".yaml");
            Files.writeString(tempFile, output, StandardCharsets.UTF_8);
            try {
                Files.move(tempFile, filePath, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException exception) {
                Files.move(tempFile, filePath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException exception) {
            throw new UncheckedIOException("Failed to write allowlist file", exception);
        }
    }

    private AllowlistEntry fromMap(Map<?, ?> map) {
        Object domain = map.get("domain");
        if (!(domain instanceof String domainValue)) {
            return null;
        }
        Object enabled = map.get("enabled");
        boolean enabledValue = enabled instanceof Boolean bool ? bool : true;
        return new AllowlistEntry(domainValue, enabledValue);
    }

    private DumperOptions buildDumperOptions() {
        DumperOptions options = new DumperOptions();
        options.setPrettyFlow(true);
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        options.setIndent(2);
        return options;
    }
}
