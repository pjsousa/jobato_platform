package com.jobato.api.service;

public class AllowlistDuplicateException extends RuntimeException {
    public AllowlistDuplicateException(String message) {
        super(message);
    }
}
