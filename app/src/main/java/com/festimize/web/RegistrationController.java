package com.festimize.web;

import com.festimize.domain.AppUser;
import com.festimize.repo.AppUserRepository;
import jakarta.validation.Valid;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

/** Creates an app_user row. Nothing else — taste is collected on /setup. */
@Controller
public class RegistrationController {

    private final AppUserRepository users;
    private final PasswordEncoder passwordEncoder;

    public RegistrationController(AppUserRepository users, PasswordEncoder passwordEncoder) {
        this.users = users;
        this.passwordEncoder = passwordEncoder;
    }

    @GetMapping("/register")
    public String showForm(@ModelAttribute("form") RegistrationForm form) {
        return "register";
    }

    @PostMapping("/register")
    @Transactional
    public String register(@Valid @ModelAttribute("form") RegistrationForm form,
                           BindingResult binding) {
        if (!binding.hasFieldErrors("email") && users.existsByEmailIgnoreCase(form.getEmail())) {
            binding.rejectValue("email", "taken", "That email already has an account.");
        }
        if (binding.hasErrors()) {
            return "register";
        }

        AppUser user = new AppUser();
        user.setEmail(form.getEmail().trim());
        user.setPasswordHash(passwordEncoder.encode(form.getPassword()));
        user.setDisplayName(form.getDisplayName() == null || form.getDisplayName().isBlank()
                ? null
                : form.getDisplayName().trim());
        users.save(user);

        return "redirect:/login?registered";
    }
}
