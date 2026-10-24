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

    /** The shortest piece of a set worth crossing the site for. */
    private static final int WORTH_CATCHING = 20;

    /**
     * The shortest piece worth it when you are going to that stage anyway.
     *
     * The twenty-minute floor exists to justify a walk. When the set is on
     * the stage your next one is on, there is no walk to justify — you were
     * going to stand there regardless, so ten minutes of a band is ten
     * minutes you would otherwise spend waiting. Slipknot finishing at 21:15
     * on the stage System of a Down opens at 21:45 is exactly that case, and
     * the flat floor was refusing it.
     */
    private static final int WORTH_STAYING_FOR = 10;

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
                          int overBy, boolean worthActingOn, String dropInstead,
                          String onSite,
                          /** ISO date, so a form can post about this day. */
                          String dayOn,
                          /** This day's own hours, blank where it keeps the profile's. */
                          String arriveAt, String leaveBy) {}

    public record Slot(String kind, String time, String artist, Long artistId,
                       Long performanceId, Long alternativeId, String alternative,
                       String stage,
                       String reason, String tradeoff, int minutes, boolean rising,
                       String addCost, String fromAt, String toAt, int catchMinutes,
                       String catchFrom, String catchTo,
                       /**
                        * When this set is only partly attended, the hours it
                        * actually runs. The row shows the part you are there
                        * for, which on its own looks like the whole set.
                        */
                       String playsFrom) {
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
        // When the day starts and when it ends, which is not the same as how
        // much music is in it. The limit counts music; what wears somebody
        // out is the span, and the rail said only the first of those.
        Map<String, java.time.OffsetDateTime[]> spanOf = new LinkedHashMap<>();
        int sets = 0, rests = 0, picks = 0, minutes = 0;

        if (plan.isPresent()) {
            for (PlanItem item : items.findForPlan(plan.get().getPlanId())) {
                String dayKey = item.getStartsAt().format(DAY);
                tabOf.putIfAbsent(dayKey, item.getStartsAt().format(TAB).toUpperCase(Locale.UK));
                int[] tally = perDay.computeIfAbsent(dayKey, d -> new int[5]);
                java.time.OffsetDateTime[] span = spanOf.computeIfAbsent(dayKey,
                        d -> new java.time.OffsetDateTime[] {item.getStartsAt(), item.getEndsAt()});
                if (item.getStartsAt().isBefore(span[0])) {
                    span[0] = item.getStartsAt();
                }
                if (item.getEndsAt().isAfter(span[1])) {
                    span[1] = item.getEndsAt();
                }
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
                        item.getStartsAt().toString(), item.getEndsAt().toString(), 0, null, null,
                        playsFrom(item)));
            }
        }

        // What catching part of a set would do to the length of the day.
        // Computed once the day's totals are known, which is why it is a
        // second pass: the thing worth warning about is not what the add
        // displaces — a clamped set displaces nothing — but that it pushes
        // the day past the hours this person said they wanted.
        int ceiling = me.musicCapMinutes();
        // Which sets in this plan the person added themselves. The cap only
        // budgets what the scheduler chose, so anything over the line is
        // theirs — and telling them to drop one of the scheduler's sets is
        // advice that cannot work: the solver refills the space.
        java.util.Set<Long> askedFor = new java.util.HashSet<>();
        for (String row : declined.pinnedPerformances(me.getUserId(), chosen.getEditionId())) {
            askedFor.add(Long.valueOf(row.split("\\|")[0]));
        }
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
                String[] window = catchWindow(slot, prevSet, nextSet);
                rewritten.add(new Slot(slot.kind(), slot.time(), slot.artist(), slot.artistId(),
                        slot.performanceId(), slot.alternativeId(), slot.alternative(),
                        slot.stage(), slot.reason(), slot.tradeoff(), slot.minutes(),
                        slot.rising(), note, slot.fromAt(), slot.toAt(),
                        window == null ? 0 : Integer.parseInt(window[2]),
                        window == null ? null : window[0],
                        window == null ? null : window[1],
                        slot.playsFrom()));
            }
            oneDay.setValue(rewritten);
        }

        // Which day the tabs are showing. One at a time, as the wireframe has
        // it; stacking three days made the page a scroll and the summary at
        // the end of it belonged to nothing in particular.
        String showing = byDay.containsKey(day) ? day
                : byDay.keySet().stream().findFirst().orElse(null);

        // The days this person gave their own arrival or departure. Everything
        // else keeps the account-wide window from the profile.
        Map<String, String[]> hoursOf = new LinkedHashMap<>();
        for (String row : plans.dayHours(me.getUserId(), chosen.getEditionId())) {
            String[] bits = row.split("\\|", -1);
            hoursOf.put(bits[0], new String[] {trimSeconds(bits[1]), trimSeconds(bits[2])});
        }

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
                            ? blameFor(byDay.get(e.getKey()), askedFor, byArtist) : null,
                    clock((int) Duration.between(spanOf.get(e.getKey())[0],
                                                 spanOf.get(e.getKey())[1]).toMinutes()),
                    spanOf.get(e.getKey())[0].toLocalDate().toString(),
                    hoursOf.getOrDefault(spanOf.get(e.getKey())[0].toLocalDate().toString(),
                                         new String[] {"", ""})[0],
                    hoursOf.getOrDefault(spanOf.get(e.getKey())[0].toLocalDate().toString(),
                                         new String[] {"", ""})[1]));
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
        model.addAttribute("fitInside",
                Boolean.TRUE.equals(plans.fitInside(me.getUserId(), chosen.getEditionId())));
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
        // Turning a set down cancels having asked for it. Adding already
        // cleared a decline; without the mirror image the change list showed
        // "Dropped Drain" and "Asked for Drain" at the same time, one of
        // which did nothing.
        declined.unpinOne(me.getUserId(), editionId, performanceId);
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

    /**
     * The hours this person is on site for one day.
     *
     * The profile window is one pair of times applied to every day of every
     * festival, and nobody attends a weekend that way. Posting both blank
     * hands the day back to the profile rather than storing a row that says
     * nothing.
     */
    @PostMapping("/schedule/hours")
    public String hours(@RequestParam Long editionId, @RequestParam String onDay,
                        @RequestParam(required = false) String arriveAt,
                        @RequestParam(required = false) String leaveBy,
                        Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        String from = arriveAt == null ? "" : arriveAt.trim();
        String to = leaveBy == null ? "" : leaveBy.trim();
        if (from.isEmpty() && to.isEmpty()) {
            plans.clearDayHours(me.getUserId(), editionId, onDay);
        } else {
            plans.setDayHours(me.getUserId(), editionId, onDay, from, to);
        }
        planning.buildPlan(me.getUserId(), editionId);
        // Back to the day that was changed, not the first one: the whole
        // point of the control is that the days differ.
        String label = java.time.LocalDate.parse(onDay).format(DAY);
        return "redirect:/schedule?editionId=" + editionId
                + "&day=" + java.net.URLEncoder.encode(label, java.nio.charset.StandardCharsets.UTF_8)
                + "&swapped";
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

    /**
     * Keep what you asked for and let the scheduler give up one of its own.
     *
     * Without this the only way back inside the limit was to undo the set
     * you had deliberately added, which is the wrong thing to give up. The
     * limit now covers the whole day and the scheduler fits its choices
     * around yours. Off by default: nothing is trimmed unless asked.
     */
    @PostMapping("/schedule/fit")
    public String fit(@RequestParam Long editionId, @RequestParam boolean on,
                      Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        plans.setFitInside(me.getUserId(), editionId, on);
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
    /**
     * What to undo when the day runs long.
     *
     * The budget applies to the sets the scheduler chose, so those can never
     * be the reason a day is over — drop one and the solver fills the space
     * again. Whatever is past the line was added by hand, so that is what
     * gets named. Only if nothing was added does the weakest set become the
     * answer, which is the case where the person's own picks alone exceed
     * what they said they could manage.
     */
    private static String blameFor(List<Slot> day, java.util.Set<Long> askedFor,
                                   Map<Long, Integer> byArtist) {
        String longest = null;
        long most = 0;
        for (Slot slot : day) {
            if ("SET".equals(slot.kind()) && slot.performanceId() != null
                    && askedFor.contains(slot.performanceId()) && slot.minutes() > most) {
                most = slot.minutes();
                longest = slot.artist();
            }
        }
        return longest != null ? longest + "|added" : weakestSetOf(day, byArtist);
    }

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
    private String[] catchWindow(Slot gap, Slot prevSet, Slot nextSet) {
        if (gap.alternativeId() == null || nextSet == null || nextSet.fromAt() == null) {
            return null;
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
            // You can leave before the end, too. Clamping the window at both
            // ends is what makes that expressible: the solver never has to
            // model walking out of a set, because the set it is given
            // already finishes when you do.
            java.time.OffsetDateTime nextStart = java.time.OffsetDateTime.parse(nextSet.fromAt());
            boolean sameStage = stage != null && stage.equals(nextSet.stage());
            java.time.OffsetDateTime doneBy =
                    sameStage ? nextStart : nextStart.minusMinutes(CHANGEOVER);
            if (to.isAfter(doneBy)) {
                to = doneBy;
            }
            int floor = sameStage ? WORTH_STAYING_FOR : WORTH_CATCHING;
            if (!to.isAfter(from) || Duration.between(from, to).toMinutes() < floor) {
                return null;
            }
            return new String[]{from.toString(), to.toString(),
                    String.valueOf(Duration.between(from, to).toMinutes())};
        }).orElse(null);
    }

    /** Minutes as "6h 20m", or "45m" when there is no hour to show. */
    /**
     * The advertised hours of a set the person is only catching part of.
     *
     * The timeline prints the part they are there for, which on its own reads
     * as the whole set: Deftones shows 19:40-20:15 and nothing says the band
     * plays until 20:40. The reason line did say so, at the end of a long
     * grey sentence nobody reads to the end of.
     *
     * Null when the whole set is attended, which is the usual case.
     */
    private static String playsFrom(PlanItem item) {
        if (!"SET".equals(item.getItemType()) || item.getPerformance() == null) {
            return null;
        }
        java.time.OffsetDateTime from = item.getPerformance().getStartsAt();
        java.time.OffsetDateTime to = item.getPerformance().getEndsAt();
        if (from == null || to == null
                || (!item.getStartsAt().isAfter(from) && !item.getEndsAt().isBefore(to))) {
            return null;
        }
        return from.format(TIME) + " – " + to.format(TIME);
    }

    /** 16:00:00 from Postgres is 16:00 to an <input type="time">. */
    private static String trimSeconds(String time) {
        return time != null && time.length() >= 5 ? time.substring(0, 5) : "";
    }

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
