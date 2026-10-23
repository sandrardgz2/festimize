package com.festimize.web;

import com.festimize.analytics.PlanningClient;
import com.festimize.domain.AppUser;
import com.festimize.domain.FestivalEdition;
import com.festimize.domain.Plan;
import com.festimize.domain.PlanItem;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.FestivalEditionRepository;
import com.festimize.repo.PlanItemRepository;
import com.festimize.repo.PlanRepository;
import com.festimize.repo.UserArtistRepository;
import java.security.Principal;
import java.time.Duration;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Controller;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

/** The built schedule: what the scheduler chose, day by day, rests included. */
@Controller
public class ScheduleController {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("EEEE d MMMM");
    /** The short form the wireframe puts on the day tabs: "SAT 14". */
    private static final DateTimeFormatter TAB = DateTimeFormatter.ofPattern("EEE d");
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");

    private final FestivalEditionRepository editions;
    private final com.festimize.repo.ArtistMomentumRepository momentum;
    private final com.festimize.repo.DeclinedRepository declined;
    private final AppUserRepository users;
    private final PlanRepository plans;
    private final PlanItemRepository items;
    private final PlanningClient planning;
    private final UserArtistRepository saved;
    private final com.festimize.repo.PerformanceRepository performances;

    public ScheduleController(FestivalEditionRepository editions,
                              com.festimize.repo.ArtistMomentumRepository momentum,
                              com.festimize.repo.DeclinedRepository declined,
                              AppUserRepository users,
                              PlanRepository plans, PlanItemRepository items, PlanningClient planning,
                              UserArtistRepository saved,
                              com.festimize.repo.PerformanceRepository performances) {
        this.editions = editions;
        this.momentum = momentum;
        this.declined = declined;
        this.users = users;
        this.plans = plans;
        this.items = items;
        this.planning = planning;
        this.saved = saved;
        this.performances = performances;
    }

    /** What one day of the plan adds up to, for the summary rail. */
    public record DayStat(String label, String tab, int sets, int breaks,
                          int discoveries, String active) {}

    public record Slot(String kind, String time, String artist, Long artistId,
                       Long performanceId, Long alternativeId, String alternative,
                       String stage,
                       String reason, String tradeoff, int minutes, boolean rising) {
        /** A plain changeover, as opposed to a break the scheduler chose. */
        public boolean gap() { return reason != null && reason.startsWith("gap"); }
    }

    @GetMapping("/schedule")
    public String schedule(@RequestParam(required = false) Long editionId,
                           @RequestParam(required = false) String error,
                           @RequestParam(required = false) String day,
                           Principal principal, Model model) {
        // Only editions with set times: a schedule cannot be built without them,
        // and after the corpus load there are 334 editions that have none.
        List<FestivalEdition> all = editions.findPlannable();
        if (all.isEmpty()) {
            model.addAttribute("activeNav", "schedule");
            return "schedule";
        }
        FestivalEdition chosen = all.stream()
                .filter(e -> editionId == null || e.getEditionId().equals(editionId))
                .findFirst().orElse(all.get(0));
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();

        Optional<Plan> plan = plans.findByUser_UserIdAndEdition_EditionId(me.getUserId(), chosen.getEditionId());
        // The rising measure for everyone on this plan, in one query. A day you
        // are about to walk is exactly where "this one is on the way up" is
        // worth knowing, and the badge was on the lineup and the artist page
        // but not here, which is the page you actually read on the day.
        java.util.Set<Long> climbing = new java.util.HashSet<>();
        for (com.festimize.domain.ArtistMomentum m : momentum.findRising()) {
            climbing.add(m.getArtist().getArtistId());
        }

        Map<String, List<Slot>> byDay = new LinkedHashMap<>();
        // The same figures as the whole-plan ones, kept a day at a time, so
        // the summary rail describes the day actually on screen. A three-day
        // total is not what somebody reads on the Saturday morning.
        Map<String, int[]> perDay = new LinkedHashMap<>();
        Map<String, String> tabOf = new LinkedHashMap<>();
        int sets = 0, rests = 0, picks = 0, minutes = 0;

        if (plan.isPresent()) {
            for (PlanItem item : items.findForPlan(plan.get().getPlanId())) {
                String dayKey = item.getStartsAt().format(DAY);
                tabOf.putIfAbsent(dayKey, item.getStartsAt().format(TAB).toUpperCase(Locale.UK));
                int[] tally = perDay.computeIfAbsent(dayKey, d -> new int[4]);
                int mins = (int) Duration.between(item.getStartsAt(), item.getEndsAt()).toMinutes();
                boolean isSet = "SET".equals(item.getItemType());
                if (isSet) {
                    sets++;
                    minutes += mins;
                    tally[0]++;
                    tally[2] += mins;
                    if (item.getReason() != null && item.getReason().startsWith("your pick")) {
                        picks++;
                    } else {
                        tally[3]++;
                    }
                } else {
                    rests++;
                    // Only breaks the scheduler placed. The slots it calls
                    // rests also include plain changeovers, and counting a
                    // walk between stages as a break said "6 breaks" about a
                    // day that had one.
                    if (item.getReason() == null || !item.getReason().startsWith("gap")) {
                        tally[1]++;
                    }
                }
                Long who = isSet && item.getPerformance() != null
                        ? item.getPerformance().getArtist().getArtistId() : null;
                byDay.computeIfAbsent(dayKey, d -> new ArrayList<>()).add(new Slot(
                        item.getItemType(),
                        item.getStartsAt().format(TIME) + " – " + item.getEndsAt().format(TIME),
                        isSet && item.getPerformance() != null ? item.getPerformance().getArtist().getName() : null,
                        who,
                        isSet && item.getPerformance() != null
                                ? item.getPerformance().getPerformanceId() : null,
                        item.getAlternativeId(),
                        alternativeOf(item),
                        isSet && item.getPerformance() != null && item.getPerformance().getStage() != null
                                ? item.getPerformance().getStage().getName() : null,
                        reasonOf(item), tradeoffOf(item), mins,
                        who != null && climbing.contains(who)));
            }
        }

        // Which day the tabs are showing. One at a time, as the wireframe has
        // it; stacking three days made the page a scroll and the summary at
        // the end of it belonged to nothing in particular.
        String showing = byDay.containsKey(day) ? day
                : byDay.keySet().stream().findFirst().orElse(null);

        List<DayStat> dayStats = new ArrayList<>();
        for (Map.Entry<String, int[]> e : perDay.entrySet()) {
            int[] t = e.getValue();
            dayStats.add(new DayStat(e.getKey(), tabOf.get(e.getKey()), t[0], t[1], t[3],
                    String.format("%dh %02dm", t[2] / 60, t[2] % 60)));
        }

        // The pace panel says what this day was actually built to, rather
        // than describing in the abstract that rules exist.
        model.addAttribute("paceCap", String.format("%.1f", me.musicCapMinutes() / 60.0));
        model.addAttribute("paceRun", me.getMaxRunMinutes() == null ? null
                : String.format("%.1f", me.getMaxRunMinutes() / 60.0));
        model.addAttribute("paceMeal", me.getMealBy());
        model.addAttribute("paceEarliest", me.getEarliestStart());
        model.addAttribute("paceLatest", me.getLatestEnd());

        model.addAttribute("activeNav", "schedule");
        model.addAttribute("editions", all);
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName", chosen.getFestival().getName() + " " + chosen.getYear());
        model.addAttribute("where", chosen.getFestival().getCity());
        model.addAttribute("days", byDay);
        model.addAttribute("dayStats", dayStats);
        model.addAttribute("showing", showing);
        model.addAttribute("slots", showing == null ? List.of() : byDay.get(showing));
        model.addAttribute("dayStat", dayStats.stream()
                .filter(d -> d.label().equals(showing)).findFirst().orElse(null));
        // Every "chosen over" sentence for the day on screen, collected into
        // the rail the wireframe calls TRADEOFFS.
        model.addAttribute("tradeoffs", showing == null ? List.of()
                : byDay.get(showing).stream().filter(sl -> sl.tradeoff() != null).toList());
        model.addAttribute("sets", sets);
        model.addAttribute("rests", rests);
        model.addAttribute("picks", picks);
        model.addAttribute("discoveries", sets - picks);
        model.addAttribute("declinedCount", declined.countFor(me.getUserId(), chosen.getEditionId())
                + declined.pinnedFor(me.getUserId(), chosen.getEditionId()));
        model.addAttribute("hours", String.format("%dh %02dm", minutes / 60, minutes % 60));
        model.addAttribute("hasPlan", !byDay.isEmpty());
        model.addAttribute("hasPicks", !saved.findSavedArtists(me.getUserId()).isEmpty());
        model.addAttribute("buildFailed", error != null);
        return "schedule";
    }

    @PostMapping("/schedule/build")
    public String build(@RequestParam Long editionId, Principal principal, Model model) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        boolean built = planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + (built ? "" : "&error=analytics");
    }

    /**
     * Turn down one set and rebuild the day around the hole it leaves.
     *
     * The decline is recorded against the plan rather than the person. "Not
     * this one, this weekend" is a different statement from "this artist is
     * not to my taste", and only the second belongs in the profile that
     * scores every other artist — putting it there would also hand the set a
     * pick's bonus in the scheduler, which is the opposite of what was asked.
     *
     * Rebuilding rather than deleting the row is the point: the slot the set
     * occupied is now free, and whatever it beat can have it.
     *
     * Not transactional here on purpose. The rebuild is an HTTP call to the
     * analytics service, which reads the database in a transaction of its
     * own; wrapping the write and the call together meant the planner could
     * not see the decline that had just been made, and the set came straight
     * back. The write commits in the repository, then the rebuild runs.
     */
    @PostMapping("/schedule/decline")
    public String decline(@RequestParam Long editionId, @RequestParam Long performanceId,
                          Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        declined.decline(me.getUserId(), editionId, performanceId);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&swapped";
    }

    /**
     * Take the artist this set beat, instead of this set.
     *
     * Pinning rather than declining the winner, because they are different
     * requests. Dropping frees the slot and lets the solver decide — which
     * gave Dying Wish's slot to Sevendust, not to the act the page named.
     * This says which artist should have it, and the day is built round that.
     */
    @PostMapping("/schedule/swap")
    public String swap(@RequestParam Long editionId, @RequestParam Long performanceId,
                       Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        declined.undecline(me.getUserId(), editionId, performanceId);
        declined.unpinClashing(me.getUserId(), editionId, performanceId);
        declined.pin(me.getUserId(), editionId, performanceId);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&swapped";
    }

    /**
     * Put one set into the plan from the lineup, and build the day round it.
     *
     * The same pin the swap uses. Before this, a set the scheduler neither
     * chose nor named as a runner-up could not be reached at all: nine of
     * Sick New World's twenty-five, including Deftones at 31%. Wanting to see
     * a band is not the same as the solver rating them highly, and the person
     * is allowed to be right about that.
     */
    @PostMapping("/schedule/add")
    public String add(@RequestParam Long editionId, @RequestParam Long performanceId,
                      Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        declined.undecline(me.getUserId(), editionId, performanceId);
        declined.unpinClashing(me.getUserId(), editionId, performanceId);
        declined.pin(me.getUserId(), editionId, performanceId);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&swapped";
    }

    /** Put everything back, for someone who has declined their way into a corner. */
    @PostMapping("/schedule/restore")
    public String restore(@RequestParam Long editionId, Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        declined.restoreAll(me.getUserId(), editionId);
        declined.unpinAll(me.getUserId(), editionId);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&restored";
    }

    /** The displaced artist's name, lifted out of the explanation sentence. */
    /**
     * Who the swap button offers, read from the row rather than the sentence.
     *
     * This used to pull the name back out of the reason text by looking for
     * " \u00b7 chosen over ". Then a pinned set started explaining itself as
     * "you asked for this, instead of Slipknot" — the same fact, different
     * words — the search missed, and the button to swap back disappeared
     * even though alternative_id was sitting right there on the row. Parsing
     * our own prose is a dependency on wording that nobody remembers having.
     */
    private String alternativeOf(PlanItem item) {
        if (item.getAlternativeId() == null) {
            return null;
        }
        return performances.artistNameFor(item.getAlternativeId()).orElse(null);
    }

    /** The match or pick label, without the explanation of what it beat. */
    private static String reasonOf(PlanItem item) {
        String r = item.getReason() == null ? "" : item.getReason();
        int at = r.indexOf(" \u00b7 chosen over ");
        return at < 0 ? r : r.substring(0, at);
    }

    /** "chosen over X" — why this set won its slot, shown quietly beneath it. */
    /**
     * The sentence explaining what this slot beat, whichever way it is put.
     *
     * Two phrasings reach here: the scheduler's own "chosen over X", and
     * "you asked for this, instead of X" for a set the person pinned, where
     * claiming the scheduler chose it would be false.
     */
    private static String tradeoffOf(PlanItem item) {
        String r = item.getReason() == null ? "" : item.getReason();
        for (String marker : new String[]{" \u00b7 chosen over ", " \u00b7 you asked for this, instead of "}) {
            int at = r.indexOf(marker);
            if (at >= 0) {
                return r.substring(at + 3);
            }
        }
        return null;
    }
}
