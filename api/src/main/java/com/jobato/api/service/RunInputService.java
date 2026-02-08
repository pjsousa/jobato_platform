package com.jobato.api.service;

import com.jobato.api.dto.RunInput;
import com.jobato.api.model.QueryDefinition;
import com.jobato.api.repository.AllowlistRepository;
import com.jobato.api.repository.QueryRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class RunInputService {
    private final QueryRepository queryRepository;
    private final AllowlistRepository allowlistRepository;

    public RunInputService(QueryRepository queryRepository, AllowlistRepository allowlistRepository) {
        this.queryRepository = queryRepository;
        this.allowlistRepository = allowlistRepository;
    }

    public List<RunInput> buildRunInputs() {
        List<QueryDefinition> queries = RunInputNormalizer.normalizeEnabledQueries(queryRepository.loadAll());
        List<String> domains = RunInputNormalizer.normalizeEnabledDomains(allowlistRepository.findAll());

        if (queries.isEmpty() || domains.isEmpty()) {
            throw new NoEnabledInputsException("At least one enabled query and one enabled allowlist domain are required to start a run. "
                + "Add or enable queries and domains first.");
        }

        List<RunInput> inputs = new ArrayList<>(queries.size() * domains.size());
        for (QueryDefinition query : queries) {
            for (String domain : domains) {
                inputs.add(new RunInput(
                    query.id(),
                    query.text(),
                    domain,
                    buildSearchQuery(domain, query.text())
                ));
            }
        }

        return List.copyOf(inputs);
    }

    private String buildSearchQuery(String domain, String queryText) {
        return "site:" + domain + " " + queryText;
    }
}
