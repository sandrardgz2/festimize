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
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");

    private final FestivalEditionRepository editions;
    private final com.festimize.repo.ArtistMomentumRepository momentum;
    private final com.festimize.repo.DeclinedRepository declined;
    private final AppUserRepository users;
    private final PlanRepository plans;
    private final PlanItemRepository items;
    private final PlanningClient planning;
    private final UserArtistRepository saved;

    public ScheduleController(FestivalEditionRepository editions,
                              com.festimize.repo.ArtistMomentumRepository momentum,
                              com.festimize.repo.DeclinedRepository declined,
                              AppUserRepository users,
                              PlanRepository plans, PlanItemRepository items, PlanningClient planning,
                              UserArtistRepository saved) {
        this.editions = editions;
        this.momentum = momentum;
        this.declined = declined;
        this.users = users;
        this.plans = plans;
        this.items = items;
        this.planning = planning;
        this.saved = saved;
    }

    public record Slot(String kind, String time, String artist, Long artistId,
                       Long performanceId, String stage,
                       String reason, String tradeoff, int minutes, boolean rising) {
        /** A plain changeover, as opposed to a break the scheduler chose. */
        public boolean gap() { return reason != null && reason.startsWith("gap"); }
    }

    @GetMapping("/schedule")
    public String schedule(@RequestParam(required = false) Long editionId,
                           @RequestParam(required = false) String error,
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
        int sets = 0, rests = 0, picks = 0, minutes = 0;

        if (plan.isPresent()) {
            for (PlanItem item : items.findForPlan(plan.get().getPlanId())) {
                String day = item.getStartsAt().format(DAY);
                int mins = (int) Duration.between(item.getStartsAt(), item.getEndsAt()).toMinutes();
                boolean isSet = "SET".equals(item.getItemType());
                if (isSet) {
                    sets++;
                    minutes += mins;
                    if (item.getReason() != null && item.getReason().startsWith("your pick")) picks++;
                } else {
                    rests++;
                }
                Long who = isSet && item.getPerformance() != null
                        ? item.getPerformance().getArtist().getArtistId() : null;
                byDay.computeIfAbsent(day, d -> new ArrayList<>()).add(new Slot(
                        item.getItemType(),
                        item.getStartsAt().format(TIME) + " – " + item.getEndsAt().format(TIME),
                        isSet && item.getPerformance() != null ? item.getPerformance().getArtist().getName() : null,
                        who,
                        isSet && item.getPerformance() != null
                                ? item.getPerformance().getPerformanceId() : null,
                        isSet && item.getPerformance() != null && item.getPerformance().getStage() != null
                                ? item.getPerformance().getStage().getName() : null,
                        reasonOf(item), tradeoffOf(item), mins,
                        who != null && climbing.contains(who)));
            }
        }

        model.addAttribute("activeNav", "schedule");
        model.addAttribute("editions", all);
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName", chosen.getFestival().getName() + " " + chosen.getYear());
        model.addAttribute("days", byDay);
        model.addAttribute("sets", sets);
        model.addAttribute("rests", rests);
        model.addAttribute("picks", picks);
        model.addAttribute("discoveries", sets - picks);
        model.addAttribute("declinedCount", declined.countFor(me.getUserId(), chosen.getEditionId()));
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

    /** Put everything back, for someone who has declined their way into a corner. */
    @PostMapping("/schedule/restore")
    public String restore(@RequestParam Long editionId, Principal principal) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        declined.restoreAll(me.getUserId(), editionId);
        planning.buildPlan(me.getUserId(), editionId);
        return "redirect:/schedule?editionId=" + editionId + "&restored";
    }

    /** The match or pick label, without the explanation of what it beat. */
    private static String reasonOf(PlanItem item) {
        String r = item.getReason() == null ? "" : item.getReason();
        int at = r.indexOf(" \u00b7 chosen over ");
        return at < 0 ? r : r.substring(0, at);
    }

    /** "chosen over X" — why this set won its slot, shown quietly beneath it. */
    private static String tradeoffOf(PlanItem item) {
        String r = item.getReason() == null ? "" : item.getReason();
        int at = r.indexOf(" \u00b7 chosen over ");
        return at < 0 ? null : r.substring(at + 3);
    }
}
