package com.festimize.web;

import com.festimize.domain.AppUser;
import com.festimize.domain.Artist;
import com.festimize.domain.ArtistMomentum;
import com.festimize.domain.ArtistTag;
import com.festimize.domain.Performance;
import com.festimize.repo.ArtistHistoryRepository;
import com.festimize.repo.ArtistMomentumRepository;
import com.festimize.repo.ArtistRepository;
import com.festimize.repo.ArtistScoreRepository;
import com.festimize.repo.ArtistTagRepository;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.PlanRepository;
import com.festimize.repo.UserArtistRepository;
import java.security.Principal;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

/**
 * One artist: who they are, every festival they have played, and whether they
 * are on the way up.
 *
 * The page is careful about what it claims. A rising label is only shown where
 * the measure has something to say — three or more years of history, three or
 * more festivals, and a climb in the strongest quarter — and for the 85% of
 * artists with less history than that it shows the bookings themselves and no
 * prediction at all. That is not modesty: eight candidate signals were tested
 * on exactly those artists and none beat simply knowing how much of last year
 * they held, so there is nothing to say that the facts do not already say.
 * See docs/evaluation/newcomer-signals.md.
 */
@Controller
public class ArtistController {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("EEE", Locale.UK);
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");

    private final ArtistRepository artists;
    private final ArtistMomentumRepository momentum;
    private final ArtistHistoryRepository history;
    private final ArtistTagRepository tags;
    private final AppUserRepository users;
    private final UserArtistRepository saved;
    private final ArtistScoreRepository scores;
    private final PlanRepository plans;
    private final com.festimize.analytics.TrajectoryClient trajectory;

    public ArtistController(ArtistRepository artists,
                            ArtistMomentumRepository momentum,
                            ArtistHistoryRepository history,
                            ArtistTagRepository tags,
                            AppUserRepository users,
                            UserArtistRepository saved,
                            ArtistScoreRepository scores,
                            PlanRepository plans,
                            com.festimize.analytics.TrajectoryClient trajectory) {
        this.artists = artists;
        this.momentum = momentum;
        this.history = history;
        this.tags = tags;
        this.users = users;
        this.saved = saved;
        this.scores = scores;
        this.plans = plans;
        this.trajectory = trajectory;
    }

    /** One line of the history: a festival, a year, and whether it happened. */
    public record Appearance(int year, String festival, String stage, boolean happened) {}

    /** A year of someone's career, as the page shows it. */
    public record Season(int year, int festivals, String names, boolean happened) {}

    /**
     * One bar of the climb.
     *
     * share is the percentage of that year's festivals the artist was booked
     * at, which is the quantity the rising measure is computed from. Drawing
     * the raw count instead put falling bars under a caption that said
     * "growing share": Jesus Piece played two festivals in 2022 and one in
     * 2024, but the corpus covers far fewer festivals in 2022, so their share
     * rose while the count fell. height is pixels.
     */
    public record Bar(int year, int festivals, double share, int height) {}

    /** A set you could actually go to, with the festival it belongs to. */
    public record SetTime(Long performanceId, Long editionId, String festival,
                          String day, String time, String stage, boolean inPlan) {}

    @GetMapping("/artist/{artistId}")
    public String artist(@PathVariable Long artistId, Principal principal, Model model) {
        Artist who = artists.findById(artistId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "No such artist"));

        List<Performance> played = history.findHistory(artistId);
        Optional<ArtistMomentum> measured = momentum.findByArtistId(artistId);

        // Grouped by year, because "five festivals in 2025" is the readable
        // unit of a career and a list of twenty rows is not.
        Map<Integer, List<Appearance>> byYear = new LinkedHashMap<>();
        for (Performance p : played) {
            Appearance seen = new Appearance(
                    p.getEdition().getYear(),
                    p.getEdition().getFestival().getName(),
                    p.getStage() == null ? null : p.getStage().getName(),
                    p.getEdition().isHappened());
            byYear.computeIfAbsent(seen.year(), y -> new ArrayList<>()).add(seen);
        }
        List<Season> seasons = new ArrayList<>();
        for (Map.Entry<Integer, List<Appearance>> year : byYear.entrySet()) {
            List<Appearance> found = year.getValue();
            seasons.add(new Season(
                    year.getKey(),
                    (int) found.stream().map(Appearance::festival).distinct().count(),
                    String.join(" · ", found.stream().map(Appearance::festival).distinct().toList()),
                    found.stream().anyMatch(Appearance::happened)));
        }

        StringBuilder sound = new StringBuilder();
        for (ArtistTag t : tags.findForArtists(List.of(artistId))) {
            sound.append(sound.length() == 0 ? "" : " · ").append(t.getTag());
        }

        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();

        // Why this artist, in the only terms the recommender actually uses:
        // which of their tags are also on artists this person named, and
        // which of those artists. Computed here rather than asked of the
        // analytics service, because it is a set intersection over a list of
        // ten and a round trip would be the expensive part.
        Set<String> theirTags = new LinkedHashSet<>();
        for (ArtistTag t : tags.findForArtists(List.of(artistId))) {
            theirTags.add(t.getTag());
        }
        List<Artist> mine = saved.findSavedArtists(me.getUserId());
        boolean isMine = mine.stream().anyMatch(a -> a.getArtistId().equals(artistId));
        Set<String> shared = new LinkedHashSet<>();
        List<String> matchedAgainst = new ArrayList<>();
        if (!mine.isEmpty()) {
            Map<Long, Set<String>> tagsOfMine = new LinkedHashMap<>();
            for (ArtistTag t : tags.findForArtists(mine.stream().map(Artist::getArtistId).toList())) {
                tagsOfMine.computeIfAbsent(t.getArtist().getArtistId(), k -> new LinkedHashSet<>())
                        .add(t.getTag());
            }
            for (Artist a : mine) {
                if (a.getArtistId().equals(artistId)) {
                    continue;
                }
                Set<String> overlap = new LinkedHashSet<>(tagsOfMine.getOrDefault(a.getArtistId(), Set.of()));
                overlap.retainAll(theirTags);
                if (!overlap.isEmpty()) {
                    shared.addAll(overlap);
                    matchedAgainst.add(a.getName());
                }
            }
        }

        // No percentage against yourself: every saved artist scores 1.0
        // against its own profile, which reads as a measurement and is a
        // tautology.
        Integer match = null;
        if (!isMine) {
            for (com.festimize.domain.ArtistScore sc
                    : scores.findByUser_UserIdOrderByMatchScoreDesc(me.getUserId())) {
                if (sc.getArtist().getArtistId().equals(artistId)) {
                    match = sc.getMatchScore()
                            .multiply(java.math.BigDecimal.valueOf(100)).intValue();
                    break;
                }
            }
        }

        // The climb, drawn from festivals a year rather than from stage size.
        // The wireframe drew stage promotion — "taller bar = bigger stage" —
        // and the data cannot support it: 95 of 39,778 bookings carry a
        // billing rank and no artist has more than two years of one. It is
        // also the measure that was tested and dropped, at 0.079 against
        // recency's 0.296. Festivals a year is what the Rising badge is
        // actually computed from, so that is what the bars show.
        // The series the badge is computed from, asked of the service that
        // computes it. See TrajectoryClient for why it is not worked out here.
        List<Bar> climb = new ArrayList<>();
        List<com.festimize.analytics.TrajectoryClient.Point> series =
                trajectory.forArtist(artistId);
        double peak = series.stream()
                .mapToDouble(com.festimize.analytics.TrajectoryClient.Point::share)
                .max().orElse(0.0);
        for (com.festimize.analytics.TrajectoryClient.Point point : series) {
            // Pixels, not percent: a percentage height inside an auto-height
            // flex column does not resolve, and every bar came out the same.
            // A year they did not play is drawn as nothing at all, which is
            // what it was.
            int height = peak <= 0 ? 0 : (int) Math.round(90 * point.share() / peak);
            climb.add(new Bar(point.year(), point.festivals(),
                    point.share(), point.share() > 0 ? Math.max(4, height) : 0));
        }

        // Sets you could go to: the editions that have times, which is where
        // "add this to my schedule" means anything.
        List<SetTime> setTimes = new ArrayList<>();
        for (Performance p : played) {
            if (p.getStartsAt() == null) {
                continue;
            }
            Long edition = p.getEdition().getEditionId();
            setTimes.add(new SetTime(
                    p.getPerformanceId(), edition,
                    p.getEdition().getFestival().getName() + " " + p.getEdition().getYear(),
                    p.getStartsAt().format(DAY), p.getStartsAt().format(TIME),
                    p.getStage() == null ? null : p.getStage().getName(),
                    plans.plannedPerformances(me.getUserId(), edition)
                            .contains(p.getPerformanceId())));
        }

        model.addAttribute("activeNav", "lineup");
        model.addAttribute("artist", who);
        model.addAttribute("match", match);
        model.addAttribute("isMine", isMine);
        model.addAttribute("sharedTags", shared);
        model.addAttribute("matchedAgainst", String.join(", ", matchedAgainst));
        model.addAttribute("climb", climb);
        model.addAttribute("setTimes", setTimes);
        model.addAttribute("tags", sound.toString());
        model.addAttribute("seasons", seasons);
        model.addAttribute("momentum", measured.orElse(null));
        model.addAttribute("label", measured.map(ArtistController::label).orElse(null));
        model.addAttribute("explains",
                measured.map(m -> explains(m, who.getFormedYear())).orElse(null));
        return "artist";
    }

    /**
     * The badge, where the measure has earned one, and nothing otherwise.
     *
     * There used to be a label for every case — "New to the circuit", "Among
     * the most-booked here", and so on. They were scope nobody asked for and
     * they were the source of the only wrong claims on this page: "New to the
     * circuit" went to Bommer, a dub producer of long standing whose scene
     * this dataset barely covers, and to 6,319 other artists who formed in
     * 2015 or earlier, among them Burt Bacharach and the Grand Ole Opry.
     *
     * An artist without a measured climb now gets no label at all. The page
     * shows their bookings, which is the thing we actually know, and the
     * backtest in docs/evaluation/newcomer-signals.md is why: on artists with
     * that little history, nothing outperformed the bookings themselves.
     */
    public static String label(ArtistMomentum m) {
        return m.isRising() ? "Rising" : null;
    }

    /** Why the badge, in a sentence, because a badge with no reason is a guess. */
    public static String explains(ArtistMomentum m, Short began) {
        if (!m.isRising()) {
            return null;
        }
        return "Booked at a growing share of the festivals in this dataset — "
                + m.getFestivals() + " different ones between " + m.getFirstYear()
                + " and " + m.getLastYear() + "."
                + (began == null ? "" : " Active since " + began + ".");
    }
}
