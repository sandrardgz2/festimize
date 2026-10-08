package com.festimize.web;

import com.festimize.domain.ArtistTag;
import com.festimize.domain.FestivalEdition;
import com.festimize.domain.Performance;
import com.festimize.repo.ArtistTagRepository;
import com.festimize.repo.FestivalEditionRepository;
import com.festimize.repo.PerformanceRepository;
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

    public LineupController(FestivalEditionRepository editions,
                            PerformanceRepository performances,
                            ArtistTagRepository tags) {
        this.editions = editions;
        this.performances = performances;
        this.tags = tags;
    }

    /** One row on the page: who is playing, when, where, and what they sound like. */
    public record LineupRow(String artist, String tags, String day, String time, String stage, boolean headliner) {}

    @GetMapping("/lineup")
    public String lineup(@RequestParam(required = false) Long editionId, Model model) {
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
                    p.isHeadliner()));
        }

        model.addAttribute("activeNav", "lineup");
        model.addAttribute("editions", all);
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName", chosen.getFestival().getName() + " " + chosen.getYear());
        model.addAttribute("location", chosen.getFestival().getCity());
        model.addAttribute("rows", rows);
        model.addAttribute("artistCount", rows.stream().map(LineupRow::artist).distinct().count());
        return "lineup";
    }
}
