package com.festimize.web;

import com.festimize.domain.FestivalEdition;
import com.festimize.repo.FestivalEditionRepository;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

/**
 * The two things the shared header needs on every page.
 *
 * The wireframes put a festival switcher in the top bar of all nine screens,
 * which means the header has to know the festivals and know where it is
 * posting back to. Collecting that per controller would be the same four
 * lines in six places; collecting it here keeps the page controllers about
 * their own pages.
 *
 * The switcher itself is only drawn where an edition is in scope — on the
 * profile page it would be a control that changes nothing, and a dead control
 * is worse than no control.
 */
@ControllerAdvice
public class NavAdvice {

    private final FestivalEditionRepository editions;

    public NavAdvice(FestivalEditionRepository editions) {
        this.editions = editions;
    }

    /** Where the switcher submits: whatever page the person is already on. */
    @ModelAttribute("currentPath")
    public String currentPath(HttpServletRequest request) {
        return request.getRequestURI();
    }

    /**
     * Only the editions somebody can actually plan. There are three of those
     * and three hundred historical ones, and a dropdown of three hundred is
     * not a switcher.
     */
    @ModelAttribute("navEditions")
    public List<FestivalEdition> navEditions() {
        return editions.findPlannable();
    }
}
