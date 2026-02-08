package com.jobato.api.service;

import com.jobato.api.config.QuotaConfigRepository;
import com.jobato.api.config.QuotaResetPolicy;
import com.jobato.api.config.QuotaSettings;
import com.jobato.api.repository.QuotaUsageRepository;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;

@Service
public class QuotaService {
    private final QuotaConfigRepository quotaConfigRepository;
    private final QuotaUsageRepository quotaUsageRepository;
    private final Clock clock;

    public QuotaService(QuotaConfigRepository quotaConfigRepository,
                        QuotaUsageRepository quotaUsageRepository,
                        Clock clock) {
        this.quotaConfigRepository = quotaConfigRepository;
        this.quotaUsageRepository = quotaUsageRepository;
        this.clock = clock;
    }

    public void ensureQuotaAvailable() {
        QuotaSettings settings = quotaConfigRepository.load();
        String quotaDay = resolveQuotaDay(Instant.now(clock), settings.resetPolicy());
        int usage = quotaUsageRepository.getDailyUsage(quotaDay);
        if (usage >= settings.dailyLimit()) {
            throw new QuotaReachedException("Daily quota reached. Try again after the quota resets.");
        }
    }

    private String resolveQuotaDay(Instant now, QuotaResetPolicy policy) {
        ZonedDateTime zonedDateTime = now.atZone(ZoneId.of(policy.timeZone()));
        LocalDate day = zonedDateTime.toLocalDate();
        if (zonedDateTime.getHour() < policy.resetHour()) {
            day = day.minusDays(1);
        }
        return day.toString();
    }
}
