package com.jobato.api.repository;

import com.jobato.api.model.QueryDefinition;

import java.util.List;

public interface QueryRepository {
    List<QueryDefinition> loadAll();

    void saveAll(List<QueryDefinition> queries);
}
