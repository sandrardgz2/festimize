package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import java.time.LocalTime;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import org.hibernate.annotations.CreationTimestamp;

/** Maps app_user. */
@Entity
@Table(name = "app_user")
public class AppUser {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Long userId;

    @Column(name = "email", nullable = false, unique = true)
    private String email;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @Column(name = "display_name")
    private String displayName;

    /**
     * How this person wants their days paced.
     *
     * Each of these drives something the scheduler already does, so the
     * settings page changes the plan rather than describing an intention.
     * The defaults are the constants that were hard-coded before the page
     * existed, which is why an account that never opens it is unaffected.
     */
    @Column(name = "stamina", nullable = false)
    private String stamina = "moderate";

    @Column(name = "max_run_minutes", nullable = false)
    private Short maxRunMinutes = 180;

    @Column(name = "meal_by", nullable = false)
    private LocalTime mealBy = LocalTime.of(18, 0);

    @Column(name = "earliest_start")
    private LocalTime earliestStart;

    @Column(name = "latest_end")
    private LocalTime latestEnd;

    /** Minutes of music a day may hold, which is what stamina means in practice. */
    public int musicCapMinutes() {
        if ("light".equals(stamina)) {
            return 300;
        }
        return "hard".equals(stamina) ? 600 : 450;
    }

    public String getStamina() { return stamina; }

    public void setStamina(String stamina) { this.stamina = stamina; }

    public Short getMaxRunMinutes() { return maxRunMinutes; }

    public void setMaxRunMinutes(Short maxRunMinutes) { this.maxRunMinutes = maxRunMinutes; }

    public LocalTime getMealBy() { return mealBy; }

    public void setMealBy(LocalTime mealBy) { this.mealBy = mealBy; }

    public LocalTime getEarliestStart() { return earliestStart; }

    public void setEarliestStart(LocalTime earliestStart) { this.earliestStart = earliestStart; }

    public LocalTime getLatestEnd() { return latestEnd; }

    public void setLatestEnd(LocalTime latestEnd) { this.latestEnd = latestEnd; }

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public void setPasswordHash(String passwordHash) {
        this.passwordHash = passwordHash;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
