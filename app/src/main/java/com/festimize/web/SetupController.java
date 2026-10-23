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
    private final com.festimize.analytics.TagClient tagClient;

    public SetupController(AppUserRepository users, ArtistRepository artists,
                           ArtistTagRepository tags, UserArtistRepository saved,
                           com.festimize.analytics.TagClient tagClient) {
        this.users = users;
        this.artists = artists;
        this.tags = tags;
        this.saved = saved;
        this.tagClient = tagClient;
    }

    /**
     * How many artists the page asks for before it stops nudging.
     *
     * Ten is what the wireframe suggests and what the scoring was tuned
     * against; it is a suggestion rather than a requirement, and the page
     * says so. Nothing enforces it.
     */
    private static final int SUGGESTED = 10;

    /** One checkbox on the setup page. */
    public record Choice(Long artistId, String name, String tags, boolean chosen) {}

    @GetMapping("/setup")
    public String setup(@org.springframework.web.bind.annotation.RequestParam(required = false) String q,
                        Principal principal, Model model) {
        AppUser me = currentUser(principal);
        List<Artist> savedArtists = saved.findSavedArtists(me.getUserId());
        Set<Long> mine = new HashSet<>();
        savedArtists.forEach(a -> mine.add(a.getArtistId()));

        // Only artists the recommender can actually score. Taste matching runs
        // on tags, so ticking an artist with none is a no-op the page would be
        // inviting you to make: loading the corpus took this list from 139 to
        // 15,799, of which 15,660 have no tags, and rendered every one of them
        // as a checkbox on a four-megabyte page.
        Map<Long, String> tagsByArtist = new LinkedHashMap<>();
        for (ArtistTag t : tags.findAll()) {
            tagsByArtist.merge(t.getArtist().getArtistId(), t.getTag(), (a, b) -> a + " · " + b);
        }
        // Without a search, only the artists the recommender can already score,
        // plus whatever is saved. With one, the whole corpus is searchable:
        // an artist with no tags gets them fetched when they are saved, so
        // offering them is no longer offering a no-op.
        List<Artist> all;
        if (q != null && q.trim().length() >= 2) {
            all = artists.search(q.trim(), org.springframework.data.domain.PageRequest.of(0, 40));
            Map<Long, String> found = new LinkedHashMap<>();
            for (ArtistTag t : tags.findForArtists(all.stream().map(Artist::getArtistId).toList())) {
                found.merge(t.getArtist().getArtistId(), t.getTag(), (a, b) -> a + " · " + b);
            }
            tagsByArtist.putAll(found);
        } else {
            all = artists.findAll().stream()
                    .filter(a -> tagsByArtist.containsKey(a.getArtistId())
                            || mine.contains(a.getArtistId()))
                    .sorted(Comparator.comparing(Artist::getName, String.CASE_INSENSITIVE_ORDER))
                    .toList();
        }
        model.addAttribute("q", q);
        model.addAttribute("searching", q != null && q.trim().length() >= 2);
        // Saving replaces the whole list, so a save made from a filtered view
        // would throw away every saved artist the filter happened to hide.
        // These ride along as hidden fields.
        java.util.Set<Long> shown = all.stream().map(Artist::getArtistId)
                .collect(java.util.stream.Collectors.toSet());
        model.addAttribute("keep", mine.stream().filter(id -> !shown.contains(id)).toList());

        List<Choice> choices = new ArrayList<>();
        for (Artist a : all) {
            choices.add(new Choice(a.getArtistId(), a.getName(),
                    tagsByArtist.getOrDefault(a.getArtistId(), ""), mine.contains(a.getArtistId())));
        }

        model.addAttribute("activeNav", "setup");
        model.addAttribute("choices", choices);
        model.addAttribute("chosenCount", mine.size());
        // The wireframe shows what you have already chosen as chips at the top
        // of the page, rather than as ticks scattered down a list you have to
        // scroll to find. The list is small and the page is about it.
        model.addAttribute("mine", savedArtists);
        model.addAttribute("mustSee", new java.util.HashSet<>(saved.mustSeeArtistIds(me.getUserId())));
        model.addAttribute("target", SUGGESTED);
        return "setup";
    }

    @PostMapping("/setup")
    @Transactional
    public String save(@RequestParam(name = "artistIds", required = false) List<Long> artistIds,
                       Principal principal) {
        AppUser me = currentUser(principal);
        List<Long> wanted = artistIds == null ? List.of() : artistIds;

        // Anything newly saved that nobody has tagged gets tagged now. Search
        // made the other 15,660 artists reachable, and an artist the
        // recommender cannot score is not a choice, it is a no-op wearing a
        // checkbox. Best effort: a failure here leaves them saved and unscored.
        for (Long id : wanted) {
            if (tags.findForArtists(List.of(id)).isEmpty()) {
                tagClient.tag(id);
            }
        }

        // Replace the whole list: simplest correct behaviour, and the list is small.
        // The must-see stars have to be carried across it by hand — they are
        // the one thing on these rows the form does not post, so a plain
        // delete-and-reinsert would silently unstar everybody on any save.
        java.util.Set<Long> stars = new java.util.HashSet<>(saved.mustSeeArtistIds(me.getUserId()));
        saved.deleteAll(saved.findByUser_UserIdOrderByAddedAtAsc(me.getUserId()));
        for (Long id : wanted) {
            artists.findById(id).ifPresent(artist -> {
                UserArtist ua = new UserArtist();
                ua.setUser(me);
                ua.setArtist(artist);
                ua.setMustSee(stars.contains(id));
                saved.save(ua);
            });
        }
        return "redirect:/lineup";
    }

    /**
     * Drop one artist, from the chip that names them.
     *
     * Separate from the save above because it is a different gesture: saving
     * replaces the whole list and has to be told everything you want kept,
     * which is why a save from a filtered page carries hidden fields. Removing
     * one artist should not require knowing about the other nine.
     */
    @PostMapping("/setup/remove")
    @Transactional
    public String remove(@RequestParam Long artistId, Principal principal) {
        AppUser me = currentUser(principal);
        saved.findByUser_UserIdOrderByAddedAtAsc(me.getUserId()).stream()
                .filter(ua -> ua.getArtist().getArtistId().equals(artistId))
                .findFirst()
                .ifPresent(saved::delete);
        return "redirect:/setup";
    }

    /**
     * Star or unstar one artist.
     *
     * Its own gesture, like removing one: it says something about that artist
     * and nothing about the other nine, so it does not go through the
     * whole-list save.
     */
    @PostMapping("/setup/must-see")
    @Transactional
    public String mustSee(@RequestParam Long artistId,
                          @RequestParam(defaultValue = "true") boolean on,
                          Principal principal) {
        AppUser me = currentUser(principal);
        saved.setMustSee(me.getUserId(), artistId, on);
        return "redirect:/setup";
    }

    private AppUser currentUser(Principal principal) {
        return users.findByEmailIgnoreCase(principal.getName())
                .orElseThrow(() -> new IllegalStateException("Signed in user not found: " + principal.getName()));
    }
}
