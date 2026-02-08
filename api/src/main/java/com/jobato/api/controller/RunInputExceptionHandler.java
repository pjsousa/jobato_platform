package com.jobato.api.controller;

import com.jobato.api.service.NoEnabledInputsException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;

@RestControllerAdvice
public class RunInputExceptionHandler {
    @ExceptionHandler(NoEnabledInputsException.class)
    public ResponseEntity<ProblemDetail> handleNoEnabledInputs(NoEnabledInputsException exception,
                                                               HttpServletRequest request) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, exception.getMessage());
        detail.setTitle("No enabled inputs");
        detail.setInstance(URI.create(request.getRequestURI()));
        detail.setProperty("errorCode", "NO_ENABLED_INPUTS");
        return ResponseEntity.badRequest().body(detail);
    }
}
