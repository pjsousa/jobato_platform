package com.jobato.api.model;

public class ResultItem {
    private final Integer id;
    private final String runId;
    private final String queryId;
    private final String queryText;
    private final String searchQuery;
    private final String domain;
    private final String title;
    private final String snippet;
    private final String rawUrl;
    private final String finalUrl;
    private final String createdAt;
    private final String rawHtmlPath;
    private final String visibleText;
    private final String cacheKey;
    private final String cachedAt;
    private final String lastSeenAt;
    private final String normalizedUrl;
    // Dedupe fields
    private final Integer canonicalId;
    private final Boolean isDuplicate;
    private final Boolean isHidden;
    private final Integer duplicateCount;

    public ResultItem(Integer id, String runId, String queryId, String queryText,
                      String searchQuery, String domain, String title, String snippet,
                      String rawUrl, String finalUrl, String createdAt, String rawHtmlPath,
                      String visibleText, String cacheKey, String cachedAt, String lastSeenAt,
                      String normalizedUrl, Integer canonicalId, Boolean isDuplicate,
                      Boolean isHidden, Integer duplicateCount) {
        this.id = id;
        this.runId = runId;
        this.queryId = queryId;
        this.queryText = queryText;
        this.searchQuery = searchQuery;
        this.domain = domain;
        this.title = title;
        this.snippet = snippet;
        this.rawUrl = rawUrl;
        this.finalUrl = finalUrl;
        this.createdAt = createdAt;
        this.rawHtmlPath = rawHtmlPath;
        this.visibleText = visibleText;
        this.cacheKey = cacheKey;
        this.cachedAt = cachedAt;
        this.lastSeenAt = lastSeenAt;
        this.normalizedUrl = normalizedUrl;
        this.canonicalId = canonicalId;
        this.isDuplicate = isDuplicate;
        this.isHidden = isHidden;
        this.duplicateCount = duplicateCount;
    }

    // Getters
    public Integer getId() { return id; }
    public String getRunId() { return runId; }
    public String getQueryId() { return queryId; }
    public String getQueryText() { return queryText; }
    public String getSearchQuery() { return searchQuery; }
    public String getDomain() { return domain; }
    public String getTitle() { return title; }
    public String getSnippet() { return snippet; }
    public String getRawUrl() { return rawUrl; }
    public String getFinalUrl() { return finalUrl; }
    public String getCreatedAt() { return createdAt; }
    public String getRawHtmlPath() { return rawHtmlPath; }
    public String getVisibleText() { return visibleText; }
    public String getCacheKey() { return cacheKey; }
    public String getCachedAt() { return cachedAt; }
    public String getLastSeenAt() { return lastSeenAt; }
    public String getNormalizedUrl() { return normalizedUrl; }
    public Integer getCanonicalId() { return canonicalId; }
    public Boolean getIsDuplicate() { return isDuplicate; }
    public Boolean getIsHidden() { return isHidden; }
    public Integer getDuplicateCount() { return duplicateCount; }
}
