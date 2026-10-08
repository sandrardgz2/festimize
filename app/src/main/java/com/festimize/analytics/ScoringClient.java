package com.festimize.analytics;

import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * Talks to the Python analytics service, which owns the taste matching.
 *
 * The web tier never scores anything itself: it asks for a recompute and then
 * reads the cached numbers out of artist_score. If the service is down the
 * page still renders, just without match percentages — a missing number is
 * better than a wrong one or a broken page.
 */
@Component
public class ScoringClient {

    private static final Logger log = LoggerFactory.getLogger(ScoringClient.class);

    private final RestTemplate http;
    private final String baseUrl;

    public ScoringClient(RestTemplateBuilder builder,
                         @Value("${festimize.analytics.base-url:http://localhost:8000}") String baseUrl) {
        this.baseUrl = baseUrl;
        this.http = builder
                .connectTimeout(Duration.ofSeconds(2))
                .readTimeout(Duration.ofSeconds(20))
                .build();
    }

    /** Asks the analytics service to rescore one user. Returns false if it could not be reached. */
    public boolean rescore(Long userId) {
        try {
            http.postForEntity(baseUrl + "/score/" + userId, new ScoreRequest(true), Void.class);
            return true;
        } catch (RuntimeException e) {
            log.warn("Analytics service unavailable at {}: {}", baseUrl, e.getMessage());
            return false;
        }
    }

    public record ScoreRequest(boolean force_recompute) {}
}
