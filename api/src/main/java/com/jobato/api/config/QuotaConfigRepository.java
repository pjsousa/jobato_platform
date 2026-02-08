package com.jobato.api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

@Component
public class QuotaConfigRepository {
    private static final String ROOT_KEY = "quota";

    private final Path filePath;
    private final Yaml yaml;

    public QuotaConfigRepository(@Value("${quota.file-path:config/quota.yaml}") String filePath) {
        this.filePath = Path.of(filePath);
        this.yaml = new Yaml();
    }

    public QuotaSettings load() {
        if (!Files.exists(filePath)) {
            throw new IllegalStateException("Quota config not found: " + filePath.toAbsolutePath());
        }

        String content;
        try {
            content = Files.readString(filePath, StandardCharsets.UTF_8);
        } catch (IOException exception) {
            throw new UncheckedIOException(exception);
        }

        if (content.isBlank()) {
            throw new IllegalStateException("Quota config is blank: " + filePath.toAbsolutePath());
        }

        Object loaded = yaml.load(content);
        if (!(loaded instanceof Map<?, ?> root)) {
            throw new IllegalStateException("Invalid quota.yaml format: expected a map at root");
        }

        Object quotaNode = root.get(ROOT_KEY);
        if (!(quotaNode instanceof Map<?, ?> quotaMap)) {
            throw new IllegalStateException("Invalid quota.yaml format: quota must be a map");
        }

        int dailyLimit = readInt(quotaMap, "dailyLimit");
        int concurrencyLimit = readInt(quotaMap, "concurrencyLimit");
        Object resetPolicyNode = quotaMap.get("resetPolicy");
        if (!(resetPolicyNode instanceof Map<?, ?> resetPolicyMap)) {
            throw new IllegalStateException("Invalid quota.yaml format: resetPolicy must be a map");
        }
        String timeZone = readString(resetPolicyMap, "timeZone");
        int resetHour = readInt(resetPolicyMap, "resetHour");

        validateLimits(dailyLimit, concurrencyLimit, resetHour, timeZone);

        return new QuotaSettings(dailyLimit, concurrencyLimit, new QuotaResetPolicy(timeZone, resetHour));
    }

    private int readInt(Map<?, ?> map, String key) {
        Object value = map.get(key);
        if (!(value instanceof Number numberValue)) {
            throw new IllegalStateException("Invalid quota.yaml format: " + key + " must be a number");
        }
        return numberValue.intValue();
    }

    private String readString(Map<?, ?> map, String key) {
        Object value = map.get(key);
        if (!(value instanceof String stringValue)) {
            throw new IllegalStateException("Invalid quota.yaml format: " + key + " must be a string");
        }
        return stringValue;
    }

    private void validateLimits(int dailyLimit, int concurrencyLimit, int resetHour, String timeZone) {
        if (dailyLimit <= 0) {
            throw new IllegalStateException("dailyLimit must be greater than zero");
        }
        if (concurrencyLimit <= 0) {
            throw new IllegalStateException("concurrencyLimit must be greater than zero");
        }
        if (resetHour < 0 || resetHour > 23) {
            throw new IllegalStateException("resetHour must be between 0 and 23");
        }
        if (timeZone.isBlank()) {
            throw new IllegalStateException("timeZone must be provided");
        }
    }
}
