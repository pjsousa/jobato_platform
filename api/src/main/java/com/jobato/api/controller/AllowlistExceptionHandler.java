package com.jobato.api.controller;

import com.jobato.api.service.AllowlistDomainValidationException;
import com.jobato.api.service.AllowlistDuplicateException;
import com.jobato.api.service.AllowlistNotFoundException;
import com.jobato.api.service.AllowlistUpdateException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;

@RestControllerAdvice
public class AllowlistExceptionHandler {
    @ExceptionHandler(AllowlistDomainValidationException.class)
    public ResponseEntity<ProblemDetail> handleInvalidDomain(AllowlistDomainValidationException exception, HttpServletRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Invalid domain", exception.getMessage(),
                "allowlist.invalidDomain", request);
    }

    @ExceptionHandler(AllowlistDuplicateException.class)
    public ResponseEntity<ProblemDetail> handleDuplicateDomain(AllowlistDuplicateException exception, HttpServletRequest request) {
        return buildProblemDetail(HttpStatus.CONFLICT, "Duplicate domain", exception.getMessage(),
                "allowlist.duplicateDomain", request);
    }

    @ExceptionHandler(AllowlistNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(AllowlistNotFoundException exception, HttpServletRequest request) {
        return buildProblemDetail(HttpStatus.NOT_FOUND, "Domain not found", exception.getMessage(),
                "allowlist.notFound", request);
    }

    @ExceptionHandler(AllowlistUpdateException.class)
    public ResponseEntity<ProblemDetail> handleInvalidUpdate(AllowlistUpdateException exception, HttpServletRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Invalid update", exception.getMessage(),
                "allowlist.invalidUpdate", request);
    }

    private ResponseEntity<ProblemDetail> buildProblemDetail(HttpStatus status,
                                                            String title,
                                                            String detail,
                                                            String errorCode,
                                                            HttpServletRequest request) {
        ProblemDetail problemDetail = ProblemDetail.forStatusAndDetail(status, detail);
        problemDetail.setTitle(title);
        problemDetail.setInstance(URI.create(request.getRequestURI()));
        problemDetail.setProperty("errorCode", errorCode);
        return ResponseEntity.status(status).body(problemDetail);
    }
}
