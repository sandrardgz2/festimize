package com.festimize.web;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

/** Skeleton. The day-by-day plan. No scheduling yet. */
@Controller
public class ScheduleController {

    @GetMapping("/schedule")
    public String schedule(Model model) {
        model.addAttribute("activeNav", "schedule");
        return "schedule";
    }
}
