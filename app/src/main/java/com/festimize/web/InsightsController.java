package com.festimize.web;

import com.festimize.domain.AppUser;
import com.festimize.domain.FestivalEdition;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.FestivalEditionRepository;
import com.festimize.repo.InsightsRepository;
import java.security.Principal;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * What the plan says about the person who made it.
 *
 * Three things the wireframe asked for and one it did not. A "sustainability"
 * score out of ten was in the design and is not here: every other number on
 * this page is read off the data, and that one would have needed a weighting
 * invented to produce it. Showing the parts — hours a day against the ceiling
 * you set — says the same thing without the arithmetic nobody could check.
 */
@Controller
public class InsightsController {

    private static final java.time.format.DateTimeFormatter SLOT =
            java.time.format.DateTimeFormatter.ofPattern("EEE HH:mm", Locale.UK);

    private final InsightsRepository insights;
    private final FestivalEditionRepository editions;
    private final AppUserRepository users;

    public InsightsController(InsightsRepository insights, FestivalEditionRepository editions,
                              AppUserRepository users) {
        this.insights = insights;
        this.editions = editions;
        this.users = users;
    }

    public record Tag(String name, double you, double lineup) {}

    public record Day(String label, int minutes, int percentOfCeiling, boolean over) {}

    public record Rising(Long artistId, String name, int match, String slot, String stage) {}

    @GetMapping("/insights")
    public String insights(@RequestParam(required = false) Long editionId,
                           Principal principal, Model model) {
        AppUser me = users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
        List<FestivalEdition> plannable = editions.findPlannable();
        model.addAttribute("activeNav", "insights");
        model.addAttribute("editions", plannable);
        if (plannable.isEmpty()) {
            return "insights";
        }
        FestivalEdition chosen = plannable.stream()
                .filter(e -> editionId == null || e.getEditionId().equals(editionId))
                .findFirst().orElse(plannable.get(0));
        model.addAttribute("chosen", chosen);
        model.addAttribute("festivalName",
                chosen.getFestival().getName() + " " + chosen.getYear());

        Object[] d = first(insights.discovery(me.getUserId(), chosen.getEditionId()));
        long sets = num(d, 0), discoveries = num(d, 1);
        model.addAttribute("sets", sets);
        model.addAttribute("discoveryPercent", sets == 0 ? 0 : Math.round(100.0 * discoveries / sets));

        Object[] c = first(insights.coverage(chosen.getEditionId()));
        long onBill = num(c, 0), rateable = num(c, 1);
        model.addAttribute("onBill", onBill);
        model.addAttribute("coveragePercent", onBill == 0 ? 0 : Math.round(100.0 * rateable / onBill));

        int ceiling = me.musicCapMinutes();
        List<Day> days = new ArrayList<>();
        for (Object[] row : insights.effortByDay(me.getUserId(), chosen.getEditionId())) {
            java.sql.Date day = (java.sql.Date) row[0];
            int minutes = ((Number) row[1]).intValue();
            days.add(new Day(
                    day.toLocalDate().getDayOfWeek().getDisplayName(TextStyle.SHORT, Locale.UK)
                            + " " + day.toLocalDate().getDayOfMonth(),
                    minutes,
                    (int) Math.min(100, Math.round(100.0 * minutes / ceiling)),
                    minutes > ceiling));
        }
        model.addAttribute("days", days);
        model.addAttribute("ceilingHours", String.format("%.1f", ceiling / 60.0));

        List<Tag> tags = new ArrayList<>();
        for (Object[] row : insights.tasteAgainstLineup(me.getUserId(), chosen.getEditionId())) {
            tags.add(new Tag((String) row[0], ((Number) row[1]).doubleValue(),
                    ((Number) row[2]).doubleValue()));
        }
        // Scaled against the strongest bar so the shape is readable; the
        // numbers beside them stay the real percentages.
        double peak = tags.stream().mapToDouble(t -> Math.max(t.you(), t.lineup())).max().orElse(1);
        model.addAttribute("tags", tags);
        model.addAttribute("tagPeak", peak <= 0 ? 1 : peak);

        List<Rising> rising = new ArrayList<>();
        for (Object[] row : insights.risingNotYours(me.getUserId(), chosen.getEditionId())) {
            // Formatted here, not in SQL: to_char renders a timestamptz in
            // the database session's zone, which put a Bloodstock set at
            // 07:45 when the festival opens at 10:30. Every other page reads
            // the offset stored with the row, and so does this one now.
            rising.add(new Rising(((Number) row[0]).longValue(), (String) row[1],
                    ((Number) row[2]).intValue(), slot(row[3]), (String) row[4]));
        }
        model.addAttribute("rising", rising);
        return "insights";
    }

    /**
     * A set time, read as the festival published it.
     *
     * The driver hands a timestamptz back as either an OffsetDateTime or a
     * Timestamp depending on how the column is read, so both are handled.
     * Doing this in SQL with to_char was the first attempt and it rendered in
     * the database session's zone — which put a Bloodstock set at 07:45 when
     * the gates open at 10:30.
     */
    private static String slot(Object value) {
        if (value instanceof java.time.OffsetDateTime at) {
            return at.format(SLOT);
        }
        if (value instanceof java.sql.Timestamp at) {
            return at.toInstant().atOffset(java.time.ZoneOffset.UTC).format(SLOT);
        }
        if (value instanceof java.time.Instant at) {
            return at.atOffset(java.time.ZoneOffset.UTC).format(SLOT);
        }
        return String.valueOf(value);
    }

    private static Object[] first(List<Object[]> rows) {
        return rows.isEmpty() ? null : rows.get(0);
    }

    private static long num(Object[] row, int at) {
        return row == null || row[at] == null ? 0 : ((Number) row[at]).longValue();
    }
}
