package com.festimize.web;

import com.festimize.domain.AppUser;
import com.festimize.domain.Artist;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.PlanRepository;
import com.festimize.repo.UserArtistRepository;
import java.security.Principal;
import java.time.LocalTime;
import java.util.List;
import org.springframework.stereotype.Controller;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * Profile and settings: who you are, who you love, and how you want to be paced.
 *
 * The pace controls are the user-facing half of task 5.1. Those rules existed
 * as constants in the scheduler — three hours before a break, a meal before
 * six, seven and a half hours of music in a day — and a person attending a
 * festival is the one who knows whether those numbers are right for them.
 * Every control here changes a plan when it is rebuilt; none of them records
 * a preference the system then ignores.
 */
@Controller
public class ProfileController {

    private final AppUserRepository users;
    private final UserArtistRepository saved;
    private final PlanRepository plans;

    public ProfileController(AppUserRepository users, UserArtistRepository saved,
                             PlanRepository plans) {
        this.users = users;
        this.saved = saved;
        this.plans = plans;
    }

    private AppUser me(Principal principal) {
        return users.findByEmailIgnoreCase(principal.getName()).orElseThrow();
    }

    @GetMapping("/profile")
    public String profile(Principal principal, Model model) {
        AppUser me = me(principal);
        List<Artist> mine = saved.findSavedArtists(me.getUserId());
        model.addAttribute("activeNav", "profile");
        model.addAttribute("me", me);
        model.addAttribute("artists", mine);
        model.addAttribute("planCount", plans.countByUser_UserId(me.getUserId()));
        model.addAttribute("musicCapHours",
                String.format("%.1f", me.musicCapMinutes() / 60.0));
        return "profile";
    }

    @PostMapping("/profile")
    @Transactional
    public String save(@RequestParam(required = false) String displayName,
                       @RequestParam(required = false) String stamina,
                       @RequestParam(required = false) Integer maxRunHours,
                       @RequestParam(required = false) String mealBy,
                       @RequestParam(required = false) String earliestStart,
                       @RequestParam(required = false) String latestEnd,
                       Principal principal) {
        AppUser me = me(principal);
        if (displayName != null && !displayName.isBlank()) {
            me.setDisplayName(displayName.trim());
        }
        if (stamina != null && List.of("light", "moderate", "hard").contains(stamina)) {
            me.setStamina(stamina);
        }
        if (maxRunHours != null && maxRunHours >= 1 && maxRunHours <= 8) {
            me.setMaxRunMinutes((short) (maxRunHours * 60));
        }
        me.setMealBy(time(mealBy, me.getMealBy()));
        // These two are deliberately clearable: an empty box means "whenever
        // the festival opens", not "keep what was there".
        me.setEarliestStart(time(earliestStart, null));
        me.setLatestEnd(time(latestEnd, null));
        users.save(me);
        return "redirect:/profile?saved";
    }

    /** A time from the form, or the fallback when the box was left empty. */
    private static LocalTime time(String value, LocalTime fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        try {
            return LocalTime.parse(value);
        } catch (RuntimeException ignored) {
            return fallback;
        }
    }
}
