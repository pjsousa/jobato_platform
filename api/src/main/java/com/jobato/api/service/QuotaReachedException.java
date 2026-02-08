package com.jobato.api.service;

public class QuotaReachedException extends RuntimeException {
    public QuotaReachedException(String message) {
        super(message);
    }
}
