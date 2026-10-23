package com.festimize.web;

import com.festimize.analytics.ScoringClient;
import com.festimize.domain.AppUser;
import com.festimize.domain.ArtistMomentum;
import com.festimize.domain.ArtistScore;
import com.festimize.domain.ArtistTag;
import com.festimize.domain.FestivalEdition;
import com.festimize.domain.Performance;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.ArtistMomentumRepository;
import com.festimize.repo.ArtistScoreRepository;
import com.festimize.repo.ArtistTagRepository;
import com.festimize.repo.UserArtistRepository;
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
    private final UserArtistRepository saved;
    private final ArtistMomentumRepository momentum;
    private final com.festimize.repo.PlanRepository plans;
    private final EditionChoice editionChoice;

    public LineupController(FestivalEditionRepository editions,
                            PerformanceRepository performances,
                            ArtistTagRepository tags,
                            AppUserRepository users,
                            ArtistScoreRepository scores,
                            ScoringClient scoring,
                            UserArtistRepository saved,
                            ArtistMomentumRepository momentum,
                            com.festimize.repo.PlanRepository plans,
                            EditionChoice editionChoice) {
        this.editions = editions;
        this.performances = performances;
        this.tags = tags;
        this.users = users;
        this.scores = scores;
        this.scoring = scoring;
        this.saved = saved;
        this.momentum = momentum;
        this.plans = plans;
        this.editionChoice = editionChoice;
    }

    /**
     * One row on the page: who is playing, when, where, what they sound like,
     * and whether they are on the way up.
     *
     * `rising` is the only thing the measure says out loud. An artist without
     * a measured climb gets no label, because the labels that used to fill
     * that space claimed things about artists that only held for this dataset.
     */
    public record LineupRow(Long artistId, Long performanceId, String artist, String tags,
                            String day, String time,
                            String stage, boolean headliner, Integer matchPercent,
                            boolean myPick, boolean rising, boolean inPlan) {}

    @GetMapping("/lineup")
    public String lineup(@RequestParam(required = false) Long editionId, Principal principal, Model model) {
        List<FestivalEdition> all = editions.findAllWithFestival();
        if (all.isEmpty()) {
            model.addAttribute("activeNav", "lineup");
            model.addAttribute("editions", all);
            model.addAttribute("rows", List.of());
            return "lineup";
        }

        java.util.Set<Long> plannable = editions.findPlannable().stream()
                .map(FestivalEdition::getEditionId)
                .collect(java.util.stream.Collectors.toSet());
        // Any edition may be asked for by id, including the 331 historical
        // bills, but the one you land on without asking is a plannable one —
        // defaulting into a 2016 lineup you cannot schedule would be a strange
        // place to start.
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        FestivalEdition chosen = all.stream()
                .filter(e -> editionId != null && e.getEditionId().equals(editionId))
                .findFirst()
                .orElseGet(() -> editionChoice.choose(
                        all.stream().filter(e -> plannable.contains(e.getEditionId())).toList(),
                        null, me.getUserId()));

        List<Performance> sets = performances.findForEditionOrderedByStart(chosen.getEditionId());

        // Which of these are already in this person's plan. A set on the bill
        // that the scheduler did not pick, and did not name as a runner-up
        // anywhere, was unreachable: nine of Sick New World's twenty-five,
        // Deftones among them. The lineup is where someone would look for it.
        java.util.Set<Long> alreadyPlanned = new java.util.HashSet<>(
                plans.plannedPerformances(
                        users.findByEmailIgnoreCase(principal.getName()).orElseThrow().getUserId(),
                        chosen.getEditionId()));

        // Ask the analytics service to refresh this user's scores, then read the cache.
        boolean analyticsUp = scoring.rescore(me.getUserId());
        java.util.Set<Long> myPicks = new java.util.HashSet<>();
        saved.findSavedArtists(me.getUserId()).forEach(a -> myPicks.add(a.getArtistId()));
        Map<Long, Integer> matchByArtist = new LinkedHashMap<>();
        for (ArtistScore s : scores.findByUser_UserIdOrderByMatchScoreDesc(me.getUserId())) {
            matchByArtist.put(s.getArtist().getArtistId(),
                    s.getMatchScore().multiply(java.math.BigDecimal.valueOf(100)).intValue());
        }

        // One query for every artist's tags, rather than one per row.
        Map<Long, String> tagsByArtist = new LinkedHashMap<>();
        Map<Long, ArtistMomentum> climbByArtist = new LinkedHashMap<>();
        if (!sets.isEmpty()) {
            List<Long> artistIds = sets.stream().map(p -> p.getArtist().getArtistId()).distinct().toList();
            for (ArtistTag t : tags.findForArtists(artistIds)) {
                tagsByArtist.merge(t.getArtist().getArtistId(), t.getTag(), (a, b) -> a + " · " + b);
            }
            // The rising measure for this bill, in one query for the same
            // reason the tags are: a lineup page is a read, not 120 of them.
            for (ArtistMomentum m : momentum.findForArtists(artistIds)) {
                climbByArtist.put(m.getArtist().getArtistId(), m);
            }
        }

        List<LineupRow> rows = new ArrayList<>();
        for (Performance p : sets) {
            OffsetDateTime start = p.getStartsAt();
            ArtistMomentum climb = climbByArtist.get(p.getArtist().getArtistId());
            rows.add(new LineupRow(
                    p.getArtist().getArtistId(),
                    p.getPerformanceId(),
                    p.getArtist().getName(),
                    tagsByArtist.getOrDefault(p.getArtist().getArtistId(), ""),
                    start == null ? "—" : start.format(DAY),
                    start == null ? "—" : start.format(TIME),
                    p.getStage() == null ? "—" : p.getStage().getName(),
                    p.isHeadliner(),
                    myPicks.contains(p.getArtist().getArtistId())
                            ? null : matchByArtist.get(p.getArtist().getArtistId()),
                    myPicks.contains(p.getArtist().getArtistId()),
                    climb != null && climb.isRising(),
                    alreadyPlanned.contains(p.getPerformanceId())));
        }

        model.addAttribute("activeNav", "lineup");
        model.addAttribute("editions", all);
        // An edition with set times is one you can plan; the historical ones
        // are reference. The switcher keeps them apart because there are three
        // of the first and three hundred of the second.
        model.addAttribute("plannable", all.stream()
                .filter(e -> plannable.contains(e.getEditionId())).toList());
        model.addAttribute("historical", all.stream()
                .filter(e -> !plannable.contains(e.getEditionId())).toList());
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName", chosen.getFestival().getName() + " " + chosen.getYear());
        model.addAttribute("location", chosen.getFestival().getCity());
        // Best match first when we have scores; otherwise keep the running order.
        if (!matchByArtist.isEmpty()) {
            // Your own picks first, then the best discoveries.
            rows = rows.stream()
                    .sorted(java.util.Comparator
                            .comparing((LineupRow r) -> r.myPick() ? 1 : 0).reversed()
                            .thenComparing(java.util.Comparator.comparing(
                                    (LineupRow r) -> r.matchPercent() == null ? -1 : r.matchPercent()).reversed()))
                    .collect(Collectors.toList());
        }
        // Somebody who has just named their artists lands here, and the next
        // thing to do is on another page. Saying so beats leaving them to
        // find the Schedule tab; it shows whenever this festival has no plan,
        // which is the same sentence either way.
        model.addAttribute("hasPicks", !myPicks.isEmpty());
        model.addAttribute("hasPlan", !alreadyPlanned.isEmpty());
        model.addAttribute("analyticsUp", analyticsUp);
        model.addAttribute("scored", !matchByArtist.isEmpty());
        model.addAttribute("rows", rows);
        model.addAttribute("artistCount", rows.stream().map(LineupRow::artist).distinct().count());
        model.addAttribute("risingCount", rows.stream().filter(LineupRow::rising).count());
        // A historical lineup read from an article has no set times and often no
        // stages either: 5,582 of those rows have neither. Three columns of
        // em-dashes is not information, so the page leaves them out instead.
        model.addAttribute("timed", sets.stream().anyMatch(p -> p.getStartsAt() != null));
        model.addAttribute("staged", sets.stream().anyMatch(p -> p.getStage() != null));
        model.addAttribute("measured", !climbByArtist.isEmpty());
        return "lineup";
    }
}
