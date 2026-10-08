package com.festimize.web;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** What the /register form posts. */
public class RegistrationForm {

    @NotBlank
    @Email
    private String email;

    @NotBlank
    @Size(min = 8, max = 100, message = "Use at least 8 characters.")
    private String password;

    @Size(max = 80)
    private String displayName;

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }
}
