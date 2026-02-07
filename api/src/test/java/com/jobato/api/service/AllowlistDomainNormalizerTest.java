package com.jobato.api.service;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class AllowlistDomainNormalizerTest {
    @Test
    void normalizesDomainByTrimmingLowercasingAndRemovingTrailingDot() {
        String normalized = AllowlistDomainNormalizer.normalize("  ExAmple.com.  ");

        assertThat(normalized).isEqualTo("example.com");
    }

    @Test
    void rejectsSchemesPathsPortsAndWildcards() {
        assertThatThrownBy(() -> AllowlistDomainNormalizer.normalize("https://example.com"))
                .isInstanceOf(AllowlistDomainValidationException.class);
        assertThatThrownBy(() -> AllowlistDomainNormalizer.normalize("example.com/jobs"))
                .isInstanceOf(AllowlistDomainValidationException.class);
        assertThatThrownBy(() -> AllowlistDomainNormalizer.normalize("example.com:443"))
                .isInstanceOf(AllowlistDomainValidationException.class);
        assertThatThrownBy(() -> AllowlistDomainNormalizer.normalize("*.example.com"))
                .isInstanceOf(AllowlistDomainValidationException.class);
    }

    @Test
    void rejectsInvalidDomains() {
        assertThatThrownBy(() -> AllowlistDomainNormalizer.normalize("bad_domain"))
                .isInstanceOf(AllowlistDomainValidationException.class);
        assertThatThrownBy(() -> AllowlistDomainNormalizer.normalize("no-tld"))
                .isInstanceOf(AllowlistDomainValidationException.class);
    }
}
