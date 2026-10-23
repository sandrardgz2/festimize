package com.festimize.analytics;

import java.time.Duration;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * One artist's share of the circuit, year by year, for the chart on their page.
 *
 * Asked of the analytics service rather than worked out here, because it is
 * the series the rising measure is computed from and the two must agree. A
 * first attempt did compute it in Java — festivals played per year — and drew
 * falling bars under a caption that said "a growing share". The denominator
 * is every booking that year, not every festival, and a year an artist did
 * not play is a zero in the series rather than a gap; the climb that earns
 * the badge is usually the climb out of those zeros.
 *
 * If the service is down the chart is left out and the rest of the page
 * renders, which is the same bargain ScoringClient makes.
 */
@Component
public class TrajectoryClient {

    private static final Logger log = LoggerFactory.getLogger(TrajectoryClient.class);

    private final RestTemplate http;
    private final String baseUrl;

    public TrajectoryClient(RestTemplateBuilder builder,
                            @Value("${festimize.analytics.base-url:http://localhost:8000}") String baseUrl) {
        this.baseUrl = baseUrl;
        this.http = builder
                .connectTimeout(Duration.ofSeconds(2))
                .readTimeout(Duration.ofSeconds(10))
                .build();
    }

    public record Point(int year, double share, int festivals) {}

    public record Trajectory(long artist_id, List<Point> years) {}

    /** The series, or an empty list if analytics could not be reached. */
    public List<Point> forArtist(Long artistId) {
        try {
            Trajectory found = http.getForObject(
                    baseUrl + "/artists/" + artistId + "/trajectory", Trajectory.class);
            return found == null || found.years() == null ? List.of() : found.years();
        } catch (RuntimeException e) {
            log.warn("Could not read trajectory for artist {}: {}", artistId, e.getMessage());
            return List.of();
        }
    }
}
