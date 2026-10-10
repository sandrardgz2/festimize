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
    private final AppUserRepository users;
    private final PlanRepository plans;
    private final PlanItemRepository items;
    private final PlanningClient planning;
    private final UserArtistRepository saved;

    public ScheduleController(FestivalEditionRepository editions, AppUserRepository users,
                              PlanRepository plans, PlanItemRepository items, PlanningClient planning,
                              UserArtistRepository saved) {
        this.editions = editions;
        this.users = users;
        this.plans = plans;
        this.items = items;
        this.planning = planning;
        this.saved = saved;
    }

    public record Slot(String kind, String time, String artist, String stage, String reason, int minutes) {}

    @GetMapping("/schedule")
    public String schedule(@RequestParam(required = false) Long editionId,
                           @RequestParam(required = false) String error,
                           Principal principal, Model model) {
        List<FestivalEdition> all = editions.findAllWithFestival();
        if (all.isEmpty()) {
            model.addAttribute("activeNav", "schedule");
            return "schedule";
        }
        FestivalEdition chosen = all.stream()
                .filter(e -> editionId == null || e.getEditionId().equals(editionId))
                .findFirst().orElse(all.get(0));
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();

        Optional<Plan> plan = plans.findByUser_UserIdAndEdition_EditionId(me.getUserId(), chosen.getEditionId());
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
                    if ("your pick".equals(item.getReason())) picks++;
                } else {
                    rests++;
                }
                byDay.computeIfAbsent(day, d -> new ArrayList<>()).add(new Slot(
                        item.getItemType(),
                        item.getStartsAt().format(TIME) + " – " + item.getEndsAt().format(TIME),
                        isSet && item.getPerformance() != null ? item.getPerformance().getArtist().getName() : null,
                        isSet && item.getPerformance() != null && item.getPerformance().getStage() != null
                                ? item.getPerformance().getStage().getName() : null,
                        item.getReason() == null ? "" : item.getReason(),
                        mins));
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
}
