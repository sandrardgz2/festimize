package com.festimize.analytics;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * Asks the analytics service to fetch an artist's tags from MusicBrainz.
 *
 * Called when somebody saves an artist nobody had tagged yet, which is the
 * only moment it matters: the corpus holds 15,799 artists and tagging all of
 * them was work nobody needed, so they are tagged when they reach a taste
 * profile instead.
 *
 * Every failure is swallowed. An artist saved without tags scores nothing
 * until the tags arrive, which is recoverable; a save that fails because
 * MusicBrainz was slow is not.
 */
@Component
public class TagClient {

    private static final Logger log = LoggerFactory.getLogger(TagClient.class);

    private final RestTemplate http;
    private final String baseUrl;

    public TagClient(RestTemplateBuilder builder,
                     @Value("${festimize.analytics.base-url:http://localhost:8000}") String baseUrl) {
        this.http = builder.build();
        this.baseUrl = baseUrl;
    }

    /** True if tags were written. False means the artist is saved but unscored. */
    public boolean tag(Long artistId) {
        try {
            http.postForObject(baseUrl + "/tags/" + artistId, null, String.class);
            return true;
        } catch (RuntimeException e) {
            log.warn("could not tag artist {}: {}", artistId, e.toString());
            return false;
        }
    }
}
