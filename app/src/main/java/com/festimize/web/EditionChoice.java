package com.festimize.web;

import com.festimize.domain.FestivalEdition;
import com.festimize.repo.PlanRepository;
import jakarta.servlet.http.HttpServletRequest;
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
 *   2. otherwise the last one they asked for this visit, because the links in
 *      the header carry no edition and switching festival on the lineup
 *      should not be forgotten the moment you open the schedule;
 *   3. otherwise the festival they are already planning, most recent first,
 *      because coming back to the site means coming back to that;
 *   4. otherwise the soonest one that has not happened yet, because the next
 *      festival is the one worth planning.
 *
 * Hardcoding an edition id would have done the same thing for the demo
 * accounts and been wrong for everybody else, and wrong again as soon as the
 * demo data changed.
 */
@Component
public class EditionChoice {

    /** Where this visit's choice is remembered. */
    private static final String REMEMBERED = "festimize.edition";

    private final PlanRepository plans;
    private final HttpServletRequest request;

    public EditionChoice(PlanRepository plans, HttpServletRequest request) {
        this.plans = plans;
        this.request = request;
    }

    /**
     * Remember a festival the person reached by some route of its own.
     *
     * The lineup resolves its own edition, because it alone can show the 331
     * historical bills that choose() will not offer. Without telling anyone,
     * switching festival there was forgotten the moment the next page loaded.
     */
    public void remember(FestivalEdition edition) {
        if (edition != null) {
            request.getSession().setAttribute(REMEMBERED, edition.getEditionId());
        }
    }

    public FestivalEdition choose(List<FestivalEdition> plannable, Long requested, Long userId) {
        if (plannable.isEmpty()) {
            return null;
        }
        // A non-positive id is never a real edition (ids start at 1); treat it
        // as no request rather than letting it fall silently to the default,
        // so a garbage value is handled explicitly.
        if (requested != null && requested > 0) {
            for (FestivalEdition e : plannable) {
                if (e.getEditionId().equals(requested)) {
                    request.getSession().setAttribute(REMEMBERED, e.getEditionId());
                    return e;
                }
            }
        }
        Object remembered = request.getSession().getAttribute(REMEMBERED);
        if (remembered instanceof Long) {
            for (FestivalEdition e : plannable) {
                if (e.getEditionId().equals(remembered)) {
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
