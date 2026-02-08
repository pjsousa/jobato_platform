package com.jobato.api.service;

public class NoEnabledInputsException extends RuntimeException {
    public NoEnabledInputsException(String message) {
        super(message);
    }
}
