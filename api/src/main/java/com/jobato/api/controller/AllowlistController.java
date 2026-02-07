package com.jobato.api.controller;

import com.jobato.api.dto.AllowlistCreateRequest;
import com.jobato.api.dto.AllowlistResponse;
import com.jobato.api.dto.AllowlistUpdateRequest;
import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.service.AllowlistService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/allowlists")
public class AllowlistController {
    private final AllowlistService allowlistService;

    public AllowlistController(AllowlistService allowlistService) {
        this.allowlistService = allowlistService;
    }

    @GetMapping
    public List<AllowlistResponse> list() {
        return allowlistService.list().stream().map(AllowlistResponse::fromEntry).toList();
    }

    @PostMapping
    public ResponseEntity<AllowlistResponse> create(@RequestBody AllowlistCreateRequest request) {
        AllowlistEntry entry = allowlistService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(AllowlistResponse.fromEntry(entry));
    }

    @PatchMapping("/{domain}")
    public AllowlistResponse update(@PathVariable String domain, @RequestBody AllowlistUpdateRequest request) {
        AllowlistEntry entry = allowlistService.update(domain, request);
        return AllowlistResponse.fromEntry(entry);
    }
}
