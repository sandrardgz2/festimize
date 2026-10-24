package com.festimize.web;

import com.festimize.domain.FestivalEdition;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.FestivalEditionRepository;
import com.festimize.repo.UserArtistRepository;
import jakarta.servlet.http.HttpServletRequest;
import java.security.Principal;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
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
    private final AppUserRepository users;
    private final UserArtistRepository saved;

    public NavAdvice(FestivalEditionRepository editions, AppUserRepository users,
                     UserArtistRepository saved) {
        this.editions = editions;
        this.users = users;
        this.saved = saved;
    }

    /** Where the switcher submits: whatever page the person is already on. */
    @ModelAttribute("currentPath")
    public String currentPath(HttpServletRequest request) {
        return request.getRequestURI();
    }

    /**
     * The artists this person marked must-see, for the star beside their name.
     *
     * Here rather than in the five controllers that name an artist: the star
     * belongs wherever one appears, which is most of the site, and a page
     * that forgot to look it up would show a plain name and quietly contradict
     * the others. Empty for a signed-out visitor, so a template can ask
     * without first checking whether anybody is logged in.
     *
     * A HashSet rather than Set.of: the home and schedule timelines carry rest
     * rows with no artist at all, and an immutable set throws rather than
     * answering false when asked whether it contains null. The whole point of
     * this living here is that a template can ask about any row it has.
     */
    @ModelAttribute("mustSee")
    public Set<Long> mustSee(Principal principal) {
        if (principal == null) {
            return new HashSet<>();
        }
        return users.findByEmailIgnoreCase(principal.getName())
                .<Set<Long>>map(me -> new HashSet<>(saved.mustSeeArtistIds(me.getUserId())))
                .orElseGet(HashSet::new);
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
