package com.festimize.analytics;

import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * Asks the analytics service to build a schedule. The service writes the plan to
 * the database; the web tier then reads it back, the same pattern as scoring.
 */
@Component
public class PlanningClient {

    private static final Logger log = LoggerFactory.getLogger(PlanningClient.class);

    private final RestTemplate http;
    private final String baseUrl;

    public PlanningClient(RestTemplateBuilder builder,
                          @Value("${festimize.analytics.base-url:http://localhost:8000}") String baseUrl) {
        this.baseUrl = baseUrl;
        this.http = builder.connectTimeout(Duration.ofSeconds(2)).readTimeout(Duration.ofSeconds(30)).build();
    }

    /** Builds (or rebuilds) the plan for one user and festival edition. */
    public boolean buildPlan(Long userId, Long editionId) {
        try {
            http.postForEntity(baseUrl + "/plan/" + userId + "?edition_id=" + editionId, null, Void.class);
            return true;
        } catch (RuntimeException e) {
            log.warn("Could not build a plan via {}: {}", baseUrl, e.getMessage());
            return false;
        }
    }
}
