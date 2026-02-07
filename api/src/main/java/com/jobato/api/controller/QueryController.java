package com.jobato.api.controller;

import com.jobato.api.dto.QueryCreateRequest;
import com.jobato.api.dto.QueryResponse;
import com.jobato.api.dto.QueryUpdateRequest;
import com.jobato.api.model.QueryDefinition;
import com.jobato.api.service.QueryService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/queries")
public class QueryController {
    private final QueryService queryService;

    public QueryController(QueryService queryService) {
        this.queryService = queryService;
    }

    @GetMapping
    public List<QueryResponse> listQueries() {
        return queryService.list().stream().map(this::toResponse).toList();
    }

    @PostMapping
    public ResponseEntity<QueryResponse> createQuery(@Valid @RequestBody QueryCreateRequest request) {
        QueryDefinition created = queryService.create(request.text());
        return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(created));
    }

    @RequestMapping(value = "/{id}", method = {RequestMethod.PUT, RequestMethod.PATCH})
    public QueryResponse updateQuery(@PathVariable String id, @RequestBody QueryUpdateRequest request) {
        QueryDefinition updated = queryService.update(id, request.text(), request.enabled());
        return toResponse(updated);
    }

    private QueryResponse toResponse(QueryDefinition query) {
        return new QueryResponse(
            query.id(),
            query.text(),
            query.enabled(),
            query.createdAt(),
            query.updatedAt()
        );
    }
}
