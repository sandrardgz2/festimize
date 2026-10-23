package com.festimize.web;

import com.festimize.domain.FestivalEdition;
import com.festimize.repo.PlanRepository;
import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;
import org.springframework.stereotype.Component;

/**
 * Which festival a page shows when nobody has said.
 *
 * Four pages needed this and each picked the first row of findPlannable(),
 * which is whatever the database returned first — Bloodstock, in August,
 * ahead of the festival both demonstration accounts actually have a plan for.
 *
 * The rule here is the one a person would expect:
 *
 *   1. what they asked for, if they asked and it is plannable;
 *   2. otherwise the festival they are already planning, most recent first,
 *      because coming back to the site means coming back to that;
 *   3. otherwise the soonest one that has not happened yet, because the next
 *      festival is the one worth planning.
 *
 * Hardcoding an edition id would have done the same thing for the demo
 * accounts and been wrong for everybody else, and wrong again as soon as the
 * demo data changed.
 */
@Component
public class EditionChoice {

    private final PlanRepository plans;

    public EditionChoice(PlanRepository plans) {
        this.plans = plans;
    }

    public FestivalEdition choose(List<FestivalEdition> plannable, Long requested, Long userId) {
        if (plannable.isEmpty()) {
            return null;
        }
        if (requested != null) {
            for (FestivalEdition e : plannable) {
                if (e.getEditionId().equals(requested)) {
                    return e;
                }
            }
        }
        if (userId != null) {
            for (Long planned : plans.recentEditionIds(userId)) {
                for (FestivalEdition e : plannable) {
                    if (e.getEditionId().equals(planned)) {
                        return e;
                    }
                }
            }
        }
        return soonest(plannable);
    }

    /** The next one to happen; an edition with no start date sorts last. */
    private static FestivalEdition soonest(List<FestivalEdition> plannable) {
        LocalDate today = LocalDate.now();
        return plannable.stream()
                .min(Comparator
                        .comparing((FestivalEdition e) -> e.getStartDate() == null
                                || e.getStartDate().isBefore(today))
                        .thenComparing(e -> e.getStartDate() == null
                                ? LocalDate.MAX : e.getStartDate()))
                .orElse(plannable.get(0));
    }
}
