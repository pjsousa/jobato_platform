package com.jobato.api.controller;

import com.jobato.api.service.QueryNotFoundException;
import com.jobato.api.service.QueryValidationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(QueryValidationException.class)
    public ResponseEntity<ProblemDetail> handleValidation(QueryValidationException exception) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, exception.getMessage());
        detail.setTitle("Validation error");
        detail.setType(URI.create("https://jobato/errors/validation"));
        return ResponseEntity.badRequest().body(detail);
    }

    @ExceptionHandler(QueryNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(QueryNotFoundException exception) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, exception.getMessage());
        detail.setTitle("Not found");
        detail.setType(URI.create("https://jobato/errors/not-found"));
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(detail);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleInvalidArguments(MethodArgumentNotValidException exception) {
        String message = exception.getBindingResult().getFieldErrors().stream()
            .findFirst()
            .map(error -> error.getField() + " " + error.getDefaultMessage())
            .orElse("Validation error");

        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, message);
        detail.setTitle("Validation error");
        detail.setType(URI.create("https://jobato/errors/validation"));
        return ResponseEntity.badRequest().body(detail);
    }
}
