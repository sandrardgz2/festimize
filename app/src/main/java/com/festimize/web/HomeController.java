package com.festimize.web;

import com.festimize.domain.AppUser;
import com.festimize.domain.ArtistScore;
import com.festimize.domain.FestivalEdition;
import com.festimize.domain.Plan;
import com.festimize.domain.PlanItem;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.ArtistScoreRepository;
import com.festimize.repo.FestivalEditionRepository;
import com.festimize.repo.InsightsRepository;
import com.festimize.repo.PerformanceRepository;
import com.festimize.repo.PlanItemRepository;
import com.festimize.repo.PlanRepository;
import com.festimize.repo.UserArtistRepository;
import java.math.BigDecimal;
import java.security.Principal;
import java.time.Duration;
import java.time.format.DateTimeFormatter;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * The landing page from the wireframes: where you are, how the plan stands,
 * and a way into each of the three things the site does.
 *
 * Until now "/" redirected to setup, which is right exactly once — the first
 * time somebody signs in — and wrong every time after that. The redirect is
 * kept for the case it was written for: a person with no saved artists has
 * nothing for this page to summarise.
 *
 * Every figure here is read from the same queries the Lineup, Schedule and
 * Insights pages use, so the three previews cannot disagree with the pages
 * they preview. The wireframe's fourth tile was a sustainability score out of
 * ten, which is not shown for the reason given in InsightsController: it
 * would need a weighting invented to produce it.
 */
@Controller
public class HomeController {

    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");
    private static final DateTimeFormatter DATE = DateTimeFormatter.ofPattern("d MMMM", Locale.UK);

    private final FestivalEditionRepository editions;
    private final AppUserRepository users;
    private final UserArtistRepository saved;
    private final ArtistScoreRepository scores;
    private final PlanRepository plans;
    private final PlanItemRepository items;
    private final PerformanceRepository performances;
    private final InsightsRepository insights;

    public HomeController(FestivalEditionRepository editions, AppUserRepository users,
                          UserArtistRepository saved, ArtistScoreRepository scores,
                          PlanRepository plans, PlanItemRepository items,
                          PerformanceRepository performances, InsightsRepository insights) {
        this.editions = editions;
        this.users = users;
        this.saved = saved;
        this.scores = scores;
        this.plans = plans;
        this.items = items;
        this.performances = performances;
        this.insights = insights;
    }

    /** One line of a preview list: a label, something trailing it, and a link. */
    public record Line(String when, String what, String note, Long artistId) {}

    @GetMapping("/")
    public String home(@RequestParam(required = false) Long editionId,
                       Principal principal, Model model) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        if (saved.findSavedArtists(me.getUserId()).isEmpty()) {
            return "redirect:/setup";         // nothing to summarise yet
        }

        List<FestivalEdition> plannable = editions.findPlannable();
        if (plannable.isEmpty()) {
            model.addAttribute("activeNav", "home");
            return "home";
        }
        FestivalEdition chosen = plannable.stream()
                .filter(e -> editionId == null || e.getEditionId().equals(editionId))
                .findFirst().orElse(plannable.get(0));

        // ------------------------------------------------------------ lineup
        Set<Long> myPicks = new HashSet<>();
        saved.findSavedArtists(me.getUserId()).forEach(a -> myPicks.add(a.getArtistId()));

        // Names come from the bill rather than from the score rows. A score's
        // artist is a lazy proxy and open-in-view is off, so reading a name
        // off one outside a transaction throws — and the bill has to be
        // loaded anyway to know who is actually playing.
        java.util.Map<Long, String> onBill = new java.util.LinkedHashMap<>();
        performances.findForEditionOrderedByStart(chosen.getEditionId())
                .forEach(p -> onBill.put(p.getArtist().getArtistId(), p.getArtist().getName()));

        List<Line> topMatches = new ArrayList<>();
        for (ArtistScore s : scores.findByUser_UserIdOrderByMatchScoreDesc(me.getUserId())) {
            Long who = s.getArtist().getArtistId();
            if (!onBill.containsKey(who) || myPicks.contains(who)) {
                continue;                     // your own picks are not a recommendation
            }
            topMatches.add(new Line(null, onBill.get(who),
                    s.getMatchScore().multiply(BigDecimal.valueOf(100)).intValue() + "%", who));
            if (topMatches.size() == 5) {
                break;
            }
        }

        // ---------------------------------------------------------- schedule
        Optional<Plan> plan = plans.findByUser_UserIdAndEdition_EditionId(
                me.getUserId(), chosen.getEditionId());
        List<Line> firstSlots = new ArrayList<>();
        int sets = 0, picks = 0, minutes = 0;
        if (plan.isPresent()) {
            for (PlanItem item : items.findForPlan(plan.get().getPlanId())) {
                boolean isSet = "SET".equals(item.getItemType());
                int mins = (int) Duration.between(item.getStartsAt(), item.getEndsAt()).toMinutes();
                if (isSet) {
                    sets++;
                    minutes += mins;
                    if (item.getReason() != null && item.getReason().startsWith("your pick")) {
                        picks++;
                    }
                }
                if (firstSlots.size() < 5) {
                    firstSlots.add(new Line(
                            item.getStartsAt().format(TIME),
                            isSet && item.getPerformance() != null
                                    ? item.getPerformance().getArtist().getName()
                                    : "rest — " + mins + " min",
                            isSet && item.getPerformance() != null
                                    && item.getPerformance().getStage() != null
                                    ? item.getPerformance().getStage().getName() : null,
                            isSet && item.getPerformance() != null
                                    ? item.getPerformance().getArtist().getArtistId() : null));
                }
            }
        }

        // ---------------------------------------------------------- insights
        Object[] d = firstRow(insights.discovery(me.getUserId(), chosen.getEditionId()));
        long planned = number(d, 0), discoveries = number(d, 1);
        Object[] c = firstRow(insights.coverage(chosen.getEditionId()));
        long billSize = number(c, 0), rateable = number(c, 1);
        int risingWaiting = insights.risingNotYours(me.getUserId(), chosen.getEditionId()).size();

        long picksOnBill = myPicks.stream().filter(onBill::containsKey).count();

        model.addAttribute("activeNav", "home");
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName",
                chosen.getFestival().getName() + " " + chosen.getYear());
        model.addAttribute("where", chosen.getFestival().getCity());
        model.addAttribute("when", dates(chosen));
        model.addAttribute("hasPlan", sets > 0);

        model.addAttribute("sets", sets);
        model.addAttribute("hours", minutes == 0 ? "—"
                : String.format("%dh %02dm", minutes / 60, minutes % 60));
        model.addAttribute("newToYou", sets - picks);
        model.addAttribute("picksOnBill", picksOnBill);
        model.addAttribute("savedCount", myPicks.size());

        model.addAttribute("billSize", billSize);
        model.addAttribute("topMatches", topMatches);
        model.addAttribute("firstSlots", firstSlots);
        model.addAttribute("discoveryPercent",
                planned == 0 ? 0 : Math.round(100.0 * discoveries / planned));
        model.addAttribute("coveragePercent",
                billSize == 0 ? 0 : Math.round(100.0 * rateable / billSize));
        model.addAttribute("risingWaiting", risingWaiting);

        model.addAttribute("others", plannable.stream()
                .filter(e -> !e.getEditionId().equals(chosen.getEditionId())).toList());
        return "home";
    }

    /** "12–15 August", or one date, or nothing if the edition carries neither. */
    private static String dates(FestivalEdition e) {
        if (e.getStartDate() == null) {
            return null;
        }
        if (e.getEndDate() == null || e.getEndDate().equals(e.getStartDate())) {
            return e.getStartDate().format(DATE);
        }
        if (e.getStartDate().getMonth() == e.getEndDate().getMonth()) {
            return e.getStartDate().getDayOfMonth() + "–" + e.getEndDate().format(DATE);
        }
        return e.getStartDate().format(DATE) + " – " + e.getEndDate().format(DATE);
    }

    private static Object[] firstRow(List<Object[]> rows) {
        return rows.isEmpty() ? null : rows.get(0);
    }

    private static long number(Object[] row, int at) {
        return row == null || row[at] == null ? 0 : ((Number) row[at]).longValue();
    }
}
