package com.festimize.web;

import com.festimize.analytics.ScoringClient;
import com.festimize.domain.AppUser;
import com.festimize.domain.ArtistScore;
import com.festimize.domain.ArtistTag;
import com.festimize.domain.FestivalEdition;
import com.festimize.domain.Performance;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.ArtistScoreRepository;
import com.festimize.repo.ArtistTagRepository;
import com.festimize.repo.FestivalEditionRepository;
import com.festimize.repo.PerformanceRepository;
import java.security.Principal;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/** The lineup for one festival edition, read from the database. Scoring comes later. */
@Controller
public class LineupController {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("EEE");
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");

    private final FestivalEditionRepository editions;
    private final PerformanceRepository performances;
    private final ArtistTagRepository tags;
    private final AppUserRepository users;
    private final ArtistScoreRepository scores;
    private final ScoringClient scoring;

    public LineupController(FestivalEditionRepository editions,
                            PerformanceRepository performances,
                            ArtistTagRepository tags,
                            AppUserRepository users,
                            ArtistScoreRepository scores,
                            ScoringClient scoring) {
        this.editions = editions;
        this.performances = performances;
        this.tags = tags;
        this.users = users;
        this.scores = scores;
        this.scoring = scoring;
    }

    /** One row on the page: who is playing, when, where, and what they sound like. */
    public record LineupRow(String artist, String tags, String day, String time, String stage,
                            boolean headliner, Integer matchPercent) {}

    @GetMapping("/lineup")
    public String lineup(@RequestParam(required = false) Long editionId, Principal principal, Model model) {
        List<FestivalEdition> all = editions.findAllWithFestival();
        if (all.isEmpty()) {
            model.addAttribute("activeNav", "lineup");
            model.addAttribute("editions", all);
            model.addAttribute("rows", List.of());
            return "lineup";
        }

        FestivalEdition chosen = all.stream()
                .filter(e -> editionId == null || e.getEditionId().equals(editionId))
                .findFirst()
                .orElse(all.get(0));

        List<Performance> sets = performances.findForEditionOrderedByStart(chosen.getEditionId());

        // Ask the analytics service to refresh this user's scores, then read the cache.
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        boolean analyticsUp = scoring.rescore(me.getUserId());
        Map<Long, Integer> matchByArtist = new LinkedHashMap<>();
        for (ArtistScore s : scores.findByUser_UserIdOrderByMatchScoreDesc(me.getUserId())) {
            matchByArtist.put(s.getArtist().getArtistId(),
                    s.getMatchScore().multiply(java.math.BigDecimal.valueOf(100)).intValue());
        }

        // One query for every artist's tags, rather than one per row.
        Map<Long, String> tagsByArtist = new LinkedHashMap<>();
        if (!sets.isEmpty()) {
            List<Long> artistIds = sets.stream().map(p -> p.getArtist().getArtistId()).distinct().toList();
            for (ArtistTag t : tags.findForArtists(artistIds)) {
                tagsByArtist.merge(t.getArtist().getArtistId(), t.getTag(), (a, b) -> a + " · " + b);
            }
        }

        List<LineupRow> rows = new ArrayList<>();
        for (Performance p : sets) {
            OffsetDateTime start = p.getStartsAt();
            rows.add(new LineupRow(
                    p.getArtist().getName(),
                    tagsByArtist.getOrDefault(p.getArtist().getArtistId(), ""),
                    start == null ? "—" : start.format(DAY),
                    start == null ? "—" : start.format(TIME),
                    p.getStage() == null ? "—" : p.getStage().getName(),
                    p.isHeadliner(),
                    matchByArtist.get(p.getArtist().getArtistId())));
        }

        model.addAttribute("activeNav", "lineup");
        model.addAttribute("editions", all);
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName", chosen.getFestival().getName() + " " + chosen.getYear());
        model.addAttribute("location", chosen.getFestival().getCity());
        // Best match first when we have scores; otherwise keep the running order.
        if (!matchByArtist.isEmpty()) {
            rows = rows.stream()
                    .sorted(java.util.Comparator.comparing(
                            (LineupRow r) -> r.matchPercent() == null ? -1 : r.matchPercent()).reversed())
                    .collect(Collectors.toList());
        }
        model.addAttribute("analyticsUp", analyticsUp);
        model.addAttribute("scored", !matchByArtist.isEmpty());
        model.addAttribute("rows", rows);
        model.addAttribute("artistCount", rows.stream().map(LineupRow::artist).distinct().count());
        return "lineup";
    }
}
