package com.jobato.api.controller;

import com.jobato.api.service.RunInProgressException;
import com.jobato.api.service.RunNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;

@RestControllerAdvice
public class RunExceptionHandler {
    @ExceptionHandler(RunInProgressException.class)
    public ResponseEntity<ProblemDetail> handleRunInProgress(RunInProgressException exception, HttpServletRequest request) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, exception.getMessage());
        detail.setTitle("Run in progress");
        detail.setInstance(URI.create(request.getRequestURI()));
        detail.setProperty("errorCode", "RUN_IN_PROGRESS");
        return ResponseEntity.status(HttpStatus.CONFLICT).body(detail);
    }

    @ExceptionHandler(RunNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleRunNotFound(RunNotFoundException exception, HttpServletRequest request) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, exception.getMessage());
        detail.setTitle("Run not found");
        detail.setInstance(URI.create(request.getRequestURI()));
        detail.setProperty("errorCode", "RUN_NOT_FOUND");
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(detail);
    }
}
