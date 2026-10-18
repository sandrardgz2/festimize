package com.festimize.web;

import com.festimize.domain.AppUser;
import com.festimize.domain.Artist;
import com.festimize.domain.ArtistTag;
import com.festimize.domain.UserArtist;
import com.festimize.repo.AppUserRepository;
import com.festimize.repo.ArtistRepository;
import com.festimize.repo.ArtistTagRepository;
import com.festimize.repo.UserArtistRepository;
import jakarta.transaction.Transactional;
import java.security.Principal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

/** Setup: choose the artists you already love. This list is the only input the scoring needs. */
@Controller
public class SetupController {

    private final AppUserRepository users;
    private final ArtistRepository artists;
    private final ArtistTagRepository tags;
    private final UserArtistRepository saved;

    public SetupController(AppUserRepository users, ArtistRepository artists,
                           ArtistTagRepository tags, UserArtistRepository saved) {
        this.users = users;
        this.artists = artists;
        this.tags = tags;
        this.saved = saved;
    }

    /** One checkbox on the setup page. */
    public record Choice(Long artistId, String name, String tags, boolean chosen) {}

    @GetMapping("/setup")
    public String setup(Principal principal, Model model) {
        AppUser me = currentUser(principal);
        Set<Long> mine = new HashSet<>();
        saved.findSavedArtists(me.getUserId()).forEach(a -> mine.add(a.getArtistId()));

        // Only artists the recommender can actually score. Taste matching runs
        // on tags, so ticking an artist with none is a no-op the page would be
        // inviting you to make: loading the corpus took this list from 139 to
        // 15,799, of which 15,660 have no tags, and rendered every one of them
        // as a checkbox on a four-megabyte page.
        Map<Long, String> tagsByArtist = new LinkedHashMap<>();
        for (ArtistTag t : tags.findAll()) {
            tagsByArtist.merge(t.getArtist().getArtistId(), t.getTag(), (a, b) -> a + " · " + b);
        }
        List<Artist> all = artists.findAll().stream()
                .filter(a -> tagsByArtist.containsKey(a.getArtistId()) || mine.contains(a.getArtistId()))
                .sorted(Comparator.comparing(Artist::getName, String.CASE_INSENSITIVE_ORDER))
                .toList();

        List<Choice> choices = new ArrayList<>();
        for (Artist a : all) {
            choices.add(new Choice(a.getArtistId(), a.getName(),
                    tagsByArtist.getOrDefault(a.getArtistId(), ""), mine.contains(a.getArtistId())));
        }

        model.addAttribute("activeNav", "setup");
        model.addAttribute("choices", choices);
        model.addAttribute("chosenCount", mine.size());
        return "setup";
    }

    @PostMapping("/setup")
    @Transactional
    public String save(@RequestParam(name = "artistIds", required = false) List<Long> artistIds,
                       Principal principal) {
        AppUser me = currentUser(principal);
        List<Long> wanted = artistIds == null ? List.of() : artistIds;

        // Replace the whole list: simplest correct behaviour, and the list is small.
        saved.deleteAll(saved.findByUser_UserIdOrderByAddedAtAsc(me.getUserId()));
        for (Long id : wanted) {
            artists.findById(id).ifPresent(artist -> {
                UserArtist ua = new UserArtist();
                ua.setUser(me);
                ua.setArtist(artist);
                saved.save(ua);
            });
        }
        return "redirect:/lineup";
    }

    private AppUser currentUser(Principal principal) {
        return users.findByEmailIgnoreCase(principal.getName())
                .orElseThrow(() -> new IllegalStateException("Signed in user not found: " + principal.getName()));
    }
}
