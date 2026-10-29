package com.festimize.analytics;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
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
                          @Value("${festimize.analytics.base-url:http://localhost:8000}") String baseUrl,
                          @Value("${festimize.analytics.key:}") String apiKey) {
        this.baseUrl = baseUrl;
        RestTemplateBuilder b = builder.connectTimeout(Duration.ofSeconds(2))
                .readTimeout(Duration.ofSeconds(30));
        // Present the shared secret the analytics service expects. Blank in
        // local development, where the service is bound to localhost; set in
        // the Docker deployment, where the two containers share a key.
        if (apiKey != null && !apiKey.isBlank()) {
            b = b.defaultHeader("X-Analytics-Key", apiKey);
        }
        this.http = b.build();
    }

    /** What one absent set would cost if it were added, and what it would gain. */
    public record AddCost(long performance_id, String artist, List<String> costs,
                          List<String> clashes, List<String> gains, boolean available,
                          int day_minutes_after) {}

    private record AddCostResponse(long user_id, long edition_id, List<AddCost> costs) {}

    /**
     * For every set not in the plan, what adding it would do to the rest of
     * the day — keyed by performance id.
     *
     * The service answers by pinning each set and re-solving, which is the
     * same code path the add button runs, so this is the actual consequence
     * rather than a prediction of it. One call covers the whole bill; 17
     * re-solves of Sick New World take 34 milliseconds. An empty map means
     * analytics is down, and the pages that use it fall back to offering the
     * action without a forecast.
     */
    public Map<Long, AddCost> addCosts(Long userId, Long editionId) {
        try {
            AddCostResponse found = http.getForObject(
                    baseUrl + "/plan/" + userId + "/cost?edition_id=" + editionId,
                    AddCostResponse.class);
            Map<Long, AddCost> byPerformance = new LinkedHashMap<>();
            if (found != null && found.costs() != null) {
                for (AddCost c : found.costs()) {
                    byPerformance.put(c.performance_id(), c);
                }
            }
            return byPerformance;
        } catch (RuntimeException e) {
            log.warn("Could not read add-costs via {}: {}", baseUrl, e.getMessage());
            return Map.of();
        }
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
