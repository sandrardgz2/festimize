package com.festimize.repo;

import com.festimize.domain.AppUser;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AppUserRepository extends JpaRepository<AppUser, Long> {

    Optional<AppUser> findByEmailIgnoreCase(String email);

    boolean existsByEmailIgnoreCase(String email);

    /**
     * The three pace times, as text, exactly as the column holds them.
     *
     * Not through the entity. The columns are `time without time zone` and
     * the application sets hibernate.jdbc.time_zone to UTC, so Hibernate
     * converts a bare LocalTime between the JVM zone and UTC on the way in
     * and back again on the way out. Java is self-consistent and never shows
     * the stored value; the planner reads the column directly and sees
     * something five hours different. Somebody asking for nothing before
     * 11:00 had their day filtered at 16:00, and no page could explain why.
     *
     * A time here means a wall-clock time at the festival. It has no zone
     * and must not be converted, so these two queries move it as text and
     * let Postgres do the only cast involved.
     */
    @org.springframework.data.jpa.repository.Query(value = """
            select coalesce(meal_by::text, '') || '|'
                || coalesce(earliest_start::text, '') || '|'
                || coalesce(latest_end::text, '')
              from app_user where user_id = :userId
            """, nativeQuery = true)
    String paceTimes(@org.springframework.data.repository.query.Param("userId") Long userId);

    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Query(value = """
            update app_user
               set meal_by        = cast(nullif(:mealBy, '') as time),
                   earliest_start = cast(nullif(:earliest, '') as time),
                   latest_end     = cast(nullif(:latest, '') as time)
             where user_id = :userId
            """, nativeQuery = true)
    void savePaceTimes(@org.springframework.data.repository.query.Param("userId") Long userId,
                       @org.springframework.data.repository.query.Param("mealBy") String mealBy,
                       @org.springframework.data.repository.query.Param("earliest") String earliest,
                       @org.springframework.data.repository.query.Param("latest") String latest);
}
