package com.jobato.api.service;

import com.jobato.api.dto.AllowlistCreateRequest;
import com.jobato.api.dto.AllowlistUpdateRequest;
import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.repository.AllowlistRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class AllowlistService {
    private final AllowlistRepository repository;

    public AllowlistService(AllowlistRepository repository) {
        this.repository = repository;
    }

    public List<AllowlistEntry> list() {
        return repository.findAll();
    }

    public AllowlistEntry create(AllowlistCreateRequest request) {
        String normalized = AllowlistDomainNormalizer.normalize(request.domain());
        List<AllowlistEntry> entries = new ArrayList<>(repository.findAll());
        if (containsDomain(entries, normalized)) {
            throw new AllowlistDuplicateException("Domain already exists");
        }
        AllowlistEntry entry = new AllowlistEntry(normalized, true);
        entries.add(entry);
        repository.saveAll(entries);
        return entry;
    }

    public AllowlistEntry update(String domain, AllowlistUpdateRequest request) {
        if (request == null || (request.domain() == null && request.enabled() == null)) {
            throw new AllowlistUpdateException("No updates provided");
        }
        String normalizedCurrent = AllowlistDomainNormalizer.normalize(domain);
        List<AllowlistEntry> entries = new ArrayList<>(repository.findAll());
        int index = indexOf(entries, normalizedCurrent);
        if (index < 0) {
            throw new AllowlistNotFoundException("Domain not found");
        }

        AllowlistEntry existing = entries.get(index);
        String updatedDomain = existing.domain();
        if (request.domain() != null) {
            updatedDomain = AllowlistDomainNormalizer.normalize(request.domain());
        }
        boolean updatedEnabled = request.enabled() != null ? request.enabled() : existing.enabled();

        if (!updatedDomain.equals(existing.domain()) && containsDomain(entries, updatedDomain)) {
            throw new AllowlistDuplicateException("Domain already exists");
        }

        AllowlistEntry updated = new AllowlistEntry(updatedDomain, updatedEnabled);
        entries.set(index, updated);
        repository.saveAll(entries);
        return updated;
    }

    private boolean containsDomain(List<AllowlistEntry> entries, String domain) {
        return entries.stream().anyMatch(entry -> entry.domain().equals(domain));
    }

    private int indexOf(List<AllowlistEntry> entries, String domain) {
        for (int i = 0; i < entries.size(); i++) {
            if (entries.get(i).domain().equals(domain)) {
                return i;
            }
        }
        return -1;
    }
}
