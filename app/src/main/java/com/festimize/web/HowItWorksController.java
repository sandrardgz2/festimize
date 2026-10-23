package com.festimize.web;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * Page 1 of the wireframes: how the site scores, ranks and schedules, and
 * whether any of it works.
 *
 * The wireframe sketched a results table of precision@10, coverage and
 * novelty measured on fourteen test users, labelled "example values". There
 * were never fourteen test users and those numbers were placeholders, so the
 * page shows the evaluation that was actually run instead: the backtest in
 * docs/evaluation/momentum-backtest.md, which held out the last three years
 * of the corpus and asked which definition of "rising" picked the artists who
 * were in fact booked more afterwards. Those figures are fixed — they are the
 * result of one experiment over a frozen training window — so they are
 * written here rather than recomputed per request.
 *
 * The corpus figures are counted live, because those do change.
 */
@Controller
public class HowItWorksController {

    /** One row of the backtest, as docs/evaluation/momentum-backtest.md reports it. */
    public record Definition(String name, String correlation, String topDecile,
                             String lift, String bookedAtAll, boolean shipped) {}

    private final JdbcTemplate db;

    public HowItWorksController(JdbcTemplate db) {
        this.db = db;
    }

    @GetMapping("/how-it-works")
    public String howItWorks(Model model) {
        model.addAttribute("activeNav", "how");

        // Only the finished festivals: the 2027 editions are demonstration
        // lineups entered by hand and counting them here would overstate the
        // corpus by three festivals that have not happened.
        model.addAttribute("artists", one(
                "select count(*) from dim_artist"));
        model.addAttribute("festivals", one(
                "select count(distinct f.festival_id) from dim_festival f "
                + "join dim_festival_edition e on e.festival_id = f.festival_id "
                + "where e.year <= 2026"));
        model.addAttribute("editions", one(
                "select count(*) from dim_festival_edition where year <= 2026"));
        model.addAttribute("performances", one(
                "select count(*) from fact_performance p "
                + "join dim_festival_edition e on e.edition_id = p.edition_id "
                + "where e.year <= 2026"));
        model.addAttribute("firstYear", one(
                "select min(year) from dim_festival_edition"));
        model.addAttribute("lastYear", one(
                "select max(year) from dim_festival_edition where year <= 2026"));

        model.addAttribute("definitions", java.util.List.of(
                new Definition("Fame — how often they are booked", "−0.032", "5%", "0.5×", "28%", false),
                new Definition("Recency — how much of last year they held", "0.296", "14%", "1.4×", "55%", false),
                new Definition("Trend line — a growing share of festivals", "0.278", "23%", "2.3×", "64%", true),
                new Definition("Recent against prior", "0.206", "10%", "1.0×", "45%", false),
                new Definition("Moving up the bill", "0.079", "14%", "1.3×", "57%", false)));
        return "howitworks";
    }

    private long one(String sql) {
        Long found = db.queryForObject(sql, Long.class);
        return found == null ? 0 : found;
    }
}
