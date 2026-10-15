package com.festimize.web;

import com.festimize.domain.Artist;
import com.festimize.domain.ArtistMomentum;
import com.festimize.domain.ArtistTag;
import com.festimize.domain.Performance;
import com.festimize.repo.ArtistHistoryRepository;
import com.festimize.repo.ArtistMomentumRepository;
import com.festimize.repo.ArtistRepository;
import com.festimize.repo.ArtistTagRepository;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
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

    private final ArtistRepository artists;
    private final ArtistMomentumRepository momentum;
    private final ArtistHistoryRepository history;
    private final ArtistTagRepository tags;

    public ArtistController(ArtistRepository artists,
                            ArtistMomentumRepository momentum,
                            ArtistHistoryRepository history,
                            ArtistTagRepository tags) {
        this.artists = artists;
        this.momentum = momentum;
        this.history = history;
        this.tags = tags;
    }

    /** One line of the history: a festival, a year, and whether it happened. */
    public record Appearance(int year, String festival, String stage, boolean happened) {}

    /** A year of someone's career, as the page shows it. */
    public record Season(int year, int festivals, String names, boolean happened) {}

    @GetMapping("/artist/{artistId}")
    public String artist(@PathVariable Long artistId, Model model) {
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

        model.addAttribute("activeNav", "lineup");
        model.addAttribute("artist", who);
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
