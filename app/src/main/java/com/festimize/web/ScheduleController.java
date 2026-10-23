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
    /**
     * How far past the daily limit a suggestion may push the day before it
     * stops being a note and starts being a problem.
     *
     * Under this, saying so is enough — a person who set 7h 30m and ends up
     * at 7h 50m has made a choice, not a mistake. Over it, the page says
     * which set to drop, because at that point the honest advice is not
     * "mind how you go" but "then something has to come out".
     */
    private static final int OVERAGE_WORTH_ACTING_ON = 30;

    /** Minutes allowed for walking between stages; mirrors the scheduler. */
    private static final int CHANGEOVER = 10;

    /** The shortest piece of a set worth going to see. */
    private static final int WORTH_CATCHING = 20;

    /**
     * The shortest stretch without music that counts as a break rather than
     * as walking between stages.
     *
     * Not a number invented for this summary: it is the scheduler's own
     * `shortest_acceptable` when it places a breather, so the page and the
     * solver agree about what a break is. Counting only the breaks the
     * scheduler deliberately placed said "1" about a day containing an hour
     * of sitting down; counting every gap said "5" about a day containing
     * three stage walks. The short ones are simply not counted — they are
     * on the timeline, where a changeover is something you can see rather
     * than a figure anybody needs totalled.
     */
    private static final int BREAK_MINUTES = 20;

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
    private final EditionChoice editionChoice;
    private final com.festimize.repo.ArtistScoreRepository scores;

    public ScheduleController(FestivalEditionRepository editions,
                              com.festimize.repo.ArtistMomentumRepository momentum,
                              com.festimize.repo.DeclinedRepository declined,
                              AppUserRepository users,
                              PlanRepository plans, PlanItemRepository items, PlanningClient planning,
                              UserArtistRepository saved,
                              com.festimize.repo.PerformanceRepository performances,
                              EditionChoice editionChoice,
                              com.festimize.repo.ArtistScoreRepository scores) {
        this.editions = editions;
        this.momentum = momentum;
        this.declined = declined;
        this.users = users;
        this.plans = plans;
        this.items = items;
        this.planning = planning;
        this.saved = saved;
        this.performances = performances;
        this.editionChoice = editionChoice;
        this.scores = scores;
    }

    /** One edit the person has made, and how to take it back. */
    public record Change(String kind, String what, Long performanceId) {}

    /** What one day of the plan adds up to, for the summary rail. */
    public record DayStat(String label, String tab, int sets, int breaks,
                          int discoveries, String active, String breakTime,
                          int overBy, boolean worthActingOn, String dropInstead) {}

    public record Slot(String kind, String time, String artist, Long artistId,
                       Long performanceId, Long alternativeId, String alternative,
                       String stage,
                       String reason, String tradeoff, int minutes, boolean rising,
                       String addCost, String fromAt, String toAt, int catchMinutes) {
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
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        FestivalEdition chosen = editionChoice.choose(all, editionId, me.getUserId());

        Optional<Plan> plan = plans.findByUser_UserIdAndEdition_EditionId(me.getUserId(), chosen.getEditionId());
        // The rising measure for everyone on this plan, in one query. A day you
        // are about to walk is exactly where "this one is on the way up" is
        // worth knowing, and the badge was on the lineup and the artist page
        // but not here, which is the page you actually read on the day.
        java.util.Set<Long> climbing = new java.util.HashSet<>();
        for (com.festimize.domain.ArtistMomentum m : momentum.findRising()) {
            climbing.add(m.getArtist().getArtistId());
        }

        // What each absent set would do to the day, asked once rather than
        // per gap. Used only for the sets offered inside a gap, which are the
        // only place the page invites somebody to add one.
        Map<Long, com.festimize.analytics.PlanningClient.AddCost> addCosts =
                plan.isPresent() ? planning.addCosts(me.getUserId(), chosen.getEditionId())
                                 : Map.of();

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
                int[] tally = perDay.computeIfAbsent(dayKey, d -> new int[5]);
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
                    // Long enough to sit down, whoever caused it. A
                    // sixty-minute hole between two stages is a break even
                    // though the scheduler did not place it there, and a
                    // fifteen-minute one is the walk.
                    if (mins >= BREAK_MINUTES) {
                        tally[1]++;
                        tally[4] += mins;
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
                        who != null && climbing.contains(who),
                        null,            // filled in by the pass below
                        item.getStartsAt().toString(), item.getEndsAt().toString(), 0));
            }
        }

        // What catching part of a set would do to the length of the day.
        // Computed once the day's totals are known, which is why it is a
        // second pass: the thing worth warning about is not what the add
        // displaces — a clamped set displaces nothing — but that it pushes
        // the day past the hours this person said they wanted.
        int ceiling = me.musicCapMinutes();
        java.util.Set<String> myPicks = new java.util.HashSet<>();
        saved.findSavedArtists(me.getUserId()).forEach(a -> myPicks.add(a.getName()));
        Map<Long, Integer> byArtist = new LinkedHashMap<>();
        for (com.festimize.domain.ArtistScore sc
                : scores.findByUser_UserIdOrderByMatchScoreDesc(me.getUserId())) {
            byArtist.put(sc.getArtist().getArtistId(),
                    sc.getMatchScore().multiply(java.math.BigDecimal.valueOf(100)).intValue());
        }
        for (Map.Entry<String, List<Slot>> oneDay : byDay.entrySet()) {
            int already = perDay.get(oneDay.getKey())[2];
            List<Slot> rewritten = new ArrayList<>();
            List<Slot> ofDay = oneDay.getValue();
            for (int at = 0; at < ofDay.size(); at++) {
                Slot slot = ofDay.get(at);
                if (!"REST".equals(slot.kind()) || slot.alternativeId() == null) {
                    rewritten.add(slot);
                    continue;
                }
                // The set that follows this gap, which is what decides
                // whether the part inside it can be taken and left in time.
                Slot nextSet = null;
                for (int ahead = at + 1; ahead < ofDay.size() && nextSet == null; ahead++) {
                    if ("SET".equals(ofDay.get(ahead).kind())) {
                        nextSet = ofDay.get(ahead);
                    }
                }
                Slot prevSet = null;
                for (int back = at - 1; back >= 0 && prevSet == null; back--) {
                    if ("SET".equals(ofDay.get(back).kind())) {
                        prevSet = ofDay.get(back);
                    }
                }
                String note = shortCost(addCosts.get(slot.alternativeId()), ceiling, myPicks);
                rewritten.add(new Slot(slot.kind(), slot.time(), slot.artist(), slot.artistId(),
                        slot.performanceId(), slot.alternativeId(), slot.alternative(),
                        slot.stage(), slot.reason(), slot.tradeoff(), slot.minutes(),
                        slot.rising(), note, slot.fromAt(), slot.toAt(),
                        catchableWithoutDisturbing(slot, prevSet, nextSet)));
            }
            oneDay.setValue(rewritten);
        }

        // Which day the tabs are showing. One at a time, as the wireframe has
        // it; stacking three days made the page a scroll and the summary at
        // the end of it belonged to nothing in particular.
        String showing = byDay.containsKey(day) ? day
                : byDay.keySet().stream().findFirst().orElse(null);

        List<DayStat> dayStats = new ArrayList<>();
        for (Map.Entry<String, int[]> e : perDay.entrySet()) {
            int[] t = e.getValue();
            int over = t[2] - me.musicCapMinutes();
            dayStats.add(new DayStat(e.getKey(), tabOf.get(e.getKey()), t[0], t[1], t[3],
                    clock(t[2]), clock(t[4]),
                    Math.max(0, over),
                    // Only worth acting on past half an hour. Somebody who
                    // set 7h 30m and lands at 7h 50m has made a choice, not
                    // a mistake, and does not need telling to undo it.
                    over > OVERAGE_WORTH_ACTING_ON,
                    over > OVERAGE_WORTH_ACTING_ON
                            ? weakestSetOf(byDay.get(e.getKey()), byArtist) : null));
        }

        // The pace panel says what this day was actually built to, rather
        // than describing in the abstract that rules exist.
        model.addAttribute("paceCap", String.format("%.1f", me.musicCapMinutes() / 60.0));
        model.addAttribute("paceRun", me.getMaxRunMinutes() == null ? null
                : String.format("%.1f", me.getMaxRunMinutes() / 60.0));
        // As text, straight off the column — see AppUserRepository.paceTimes.
        // Reading these through the entity showed the person a different
        // number from the one the planner obeyed.
        String[] pace = (users.paceTimes(me.getUserId()) + "||").split("\\|", -1);
        model.addAttribute("paceMeal", pace[0].isEmpty() ? null : pace[0].substring(0, 5));
        model.addAttribute("paceEarliest", pace[1].isEmpty() ? null : pace[1].substring(0, 5));
        model.addAttribute("paceLatest", pace[2].isEmpty() ? null : pace[2].substring(0, 5));

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
        // Every edit, named, so each can be taken back on its own.
        List<Change> changes = new ArrayList<>();
        for (Long perf : declined.declinedPerformances(me.getUserId(), chosen.getEditionId())) {
            performances.artistNameFor(perf).ifPresent(name ->
                    changes.add(new Change("declined", "Dropped " + name, perf)));
        }
        for (String row : declined.pinnedPerformances(me.getUserId(), chosen.getEditionId())) {
            String[] parts = row.split("\\|");
            Long perf = Long.valueOf(parts[0]);
            boolean partial = parts.length > 1 && "part".equals(parts[1]);
            performances.artistNameFor(perf).ifPresent(name ->
                    changes.add(new Change("pinned",
                            (partial ? "Catching part of " : "Asked for ") + name, perf)));
        }
        model.addAttribute("changes", changes);
        model.addAttribute("mealChosen", !plans.chosenMeals(me.getUserId(),
                chosen.getEditionId()).isEmpty());
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

    /**
     * Catch the part of a set that fits in a gap, without disturbing the day.
     *
     * The ordinary add pins the whole set, which is right when somebody asks
     * for an artist by name and wrong here: the page has just said that 40 of
     * its 60 minutes fall in this gap, and accepting that offer used to
     * remove whatever the other 20 minutes clashed with. On the account this
     * was found on, that was one of the person's own picks.
     *
     * Pinning a window instead clamps the candidate before the solver runs,
     * so the set the day sees is the part that fits. It displaces nothing,
     * because there is nothing left of it to clash with.
     */
    @PostMapping("/schedule/squeeze")
    public String squeeze(@RequestParam Long editionId, @RequestParam Long performanceId,
                          @RequestParam String from, @RequestParam String to,
                          Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        declined.undecline(me.getUserId(), editionId, performanceId);
        declined.pinWindow(me.getUserId(), editionId, performanceId,
                java.time.OffsetDateTime.parse(from), java.time.OffsetDateTime.parse(to));
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&swapped";
    }

    /**
     * Eat in this gap instead of where the scheduler put the break.
     *
     * The default placement — the first real opportunity after the middle of
     * the day, before the hour you said you want to have eaten by — is a
     * reasonable guess about an afternoon that is not ours. Where there is
     * more than one gap to choose between, the person knows better.
     */
    @PostMapping("/schedule/eat-here")
    public String eatHere(@RequestParam Long editionId, @RequestParam String startsAt,
                          Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        plans.chooseMeal(me.getUserId(), editionId, startsAt);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&swapped";
    }

    /** Hand that day's meal back to the scheduler. */
    @PostMapping("/schedule/eat-anywhere")
    public String eatAnywhere(@RequestParam Long editionId, @RequestParam String onDay,
                              Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        plans.clearMeal(me.getUserId(), editionId, onDay);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&swapped";
    }

    /** Put one set back, without undoing every other decision. */
    @PostMapping("/schedule/undo")
    public String undo(@RequestParam Long editionId, @RequestParam Long performanceId,
                       @RequestParam String kind, Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        if ("declined".equals(kind)) {
            declined.undecline(me.getUserId(), editionId, performanceId);
        } else {
            declined.unpinOne(me.getUserId(), editionId, performanceId);
        }
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
    /**
     * One clause beside the set a gap offers: what it displaces, and whether
     * it pushes the day past the limit.
     *
     * Short on purpose. The detail belongs by the summary, where a person
     * reads the shape of their day; here they are deciding about one set and
     * need two facts.
     *
     * The day length is the re-solved figure from the service, not this
     * page's arithmetic. Adding a set is not simply more minutes — the solver
     * drops what no longer fits, so adding Korn to a 445-minute day leaves it
     * at 450 rather than the 475 that adding its catchable half would suggest.
     */
    private static String shortCost(com.festimize.analytics.PlanningClient.AddCost cost,
                                    int ceiling, java.util.Set<String> myPicks) {
        if (cost == null || !cost.available()) {
            return null;
        }
        // Say the whole change, not half of it. Three different things can
        // happen and they were all being reported as "costs X":
        //
        //   a clash   — the set genuinely overlaps something you are keeping
        //   a drop    — the solver re-optimises and something falls out
        //   a gain    — something else fits that did not before
        //
        // Adding Drain drops Vended and brings in Scowl, which is nine sets
        // becoming ten. Reporting only the loss made a net improvement read
        // as a penalty. Names of the person's own picks are marked, because
        // giving one of those up is not a casual aside.
        List<String> clash = new ArrayList<>();
        List<String> dropped = new ArrayList<>();
        for (String name : cost.costs()) {
            String shown = myPicks.contains(name) ? name + " (your pick)" : name;
            (cost.clashes().contains(name) ? clash : dropped).add(shown);
        }
        List<String> parts = new ArrayList<>();
        if (!clash.isEmpty()) {
            parts.add("clashes with " + String.join(" and ", clash));
        }
        if (!dropped.isEmpty()) {
            parts.add("drops " + String.join(" and ", dropped));
        }
        if (!cost.gains().isEmpty()) {
            parts.add("brings in " + String.join(" and ", cost.gains()));
        }
        if (parts.isEmpty()) {
            parts.add("nothing else changes");
        }
        String what = String.join(", ", parts);
        int over = cost.day_minutes_after() - ceiling;
        if (over > 0) {
            what += String.format(" · %d min over your limit", over);
        }
        return what;
    }

    /**
     * The set in this day with the least to recommend it, which is the one to
     * drop if something has to go.
     *
     * Never one of the person's own picks: somebody who came for a band is
     * not going to be told to skip them because the arithmetic is tidier
     * that way. Null when every set in the day is a pick, and the advice
     * then stays general.
     */
    private static String weakestSetOf(List<Slot> day, Map<Long, Integer> byArtist) {
        String weakest = null;
        int lowest = Integer.MAX_VALUE;
        for (Slot slot : day) {
            if (!"SET".equals(slot.kind()) || slot.artistId() == null
                    || (slot.reason() != null && slot.reason().startsWith("your pick"))) {
                continue;
            }
            int score = byArtist.getOrDefault(slot.artistId(), 0);
            if (score < lowest) {
                lowest = score;
                weakest = slot.artist();
            }
        }
        return weakest;
    }

    /**
     * Can the part of this set that falls inside the gap be taken without
     * disturbing anything?
     *
     * Only when it ends clear of the next set -- with walking time unless it
     * is on the same stage -- and leaves at least twenty minutes worth going
     * for. Evanescence in a 17:20-18:00 gap fails this: it runs to 18:00 and
     * the next set begins at 18:00, so taking it would mean leaving early,
     * which the solver cannot express. Eyehategod in a 13:15-14:15 gap
     * passes: clamped it runs 13:15-13:45, and the next set is at 14:15 on
     * the same stage.
     *
     * Returns the minutes you would catch, or 0 when it cannot be offered.
     */
    private int catchableWithoutDisturbing(Slot gap, Slot prevSet, Slot nextSet) {
        if (gap.alternativeId() == null || nextSet == null || nextSet.fromAt() == null) {
            return 0;
        }
        return performances.findById(gap.alternativeId()).map(p -> {
            java.time.OffsetDateTime gapStart = java.time.OffsetDateTime.parse(gap.fromAt());
            java.time.OffsetDateTime gapEnd = java.time.OffsetDateTime.parse(gap.toAt());
            java.time.OffsetDateTime from =
                    p.getStartsAt().isAfter(gapStart) ? p.getStartsAt() : gapStart;
            java.time.OffsetDateTime to =
                    p.getEndsAt().isBefore(gapEnd) ? p.getEndsAt() : gapEnd;
            String stage = performances.stageNameFor(gap.alternativeId()).orElse(null);
            // You have to walk there. Quoting the length of the window and
            // not the length of the visit promised thirty minutes of a band
            // you would see twenty of.
            if (prevSet != null && prevSet.toAt() != null) {
                java.time.OffsetDateTime leaving = java.time.OffsetDateTime.parse(prevSet.toAt());
                boolean sameAsPrev = stage != null && stage.equals(prevSet.stage());
                java.time.OffsetDateTime arrive =
                        sameAsPrev ? leaving : leaving.plusMinutes(CHANGEOVER);
                if (arrive.isAfter(from)) {
                    from = arrive;
                }
            }
            if (!to.isAfter(from)) {
                return 0;
            }
            int minutes = (int) Duration.between(from, to).toMinutes();
            if (minutes < WORTH_CATCHING) {
                return 0;
            }
            java.time.OffsetDateTime nextStart = java.time.OffsetDateTime.parse(nextSet.fromAt());
            boolean sameStage = stage != null && stage.equals(nextSet.stage());
            java.time.OffsetDateTime doneBy =
                    sameStage ? nextStart : nextStart.minusMinutes(CHANGEOVER);
            return to.isAfter(doneBy) ? 0 : minutes;
        }).orElse(0);
    }

    /** Minutes as "6h 20m", or "45m" when there is no hour to show. */
    private static String clock(int minutes) {
        return minutes >= 60 ? String.format("%dh %02dm", minutes / 60, minutes % 60)
                             : String.format("%dm", minutes);
    }

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
