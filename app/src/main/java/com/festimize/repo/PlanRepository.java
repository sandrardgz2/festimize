package com.festimize.repo;

import com.festimize.domain.Plan;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PlanRepository extends JpaRepository<Plan, Long> {

    long countByUser_UserId(Long userId);

    /** The performances already in this person's plan for one edition. */
    @org.springframework.data.jpa.repository.Query(value = """
            select i.performance_id from plan_item i join plan pl on pl.plan_id = i.plan_id
             where pl.user_id = :userId and pl.edition_id = :editionId
               and i.performance_id is not null
            """, nativeQuery = true)
    java.util.List<Long> plannedPerformances(
            @org.springframework.data.repository.query.Param("userId") Long userId,
            @org.springframework.data.repository.query.Param("editionId") Long editionId);

    Optional<Plan> findByUser_UserIdAndEdition_EditionId(Long userId, Long editionId);

    List<Plan> findByUser_UserIdOrderByUpdatedAtDesc(Long userId);

    /**
     * Editions this person has a plan for, most recently touched first.
     *
     * Ids rather than entities: Plan.edition is lazy and open-in-view is off,
     * so reading it outside a transaction throws. The path expression makes
     * the join explicit.
     */
    @org.springframework.data.jpa.repository.Query(
            "select p.edition.editionId from Plan p where p.user.userId = :userId "
            + "order by p.updatedAt desc")
    java.util.List<Long> recentEditionIds(
            @org.springframework.data.repository.query.Param("userId") Long userId);

    /**
     * Where this person wants to eat on one day of one plan.
     *
     * One row per day, replaced rather than added to: picking a second gap
     * means changing your mind, not eating twice.
     */
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Query(value = """
            insert into plan_meal (plan_id, meal_on, starts_at)
            select pl.plan_id, cast(:startsAt as timestamptz)::date, cast(:startsAt as timestamptz)
              from plan pl
             where pl.user_id = :userId and pl.edition_id = :editionId
            on conflict (plan_id, meal_on) do update set starts_at = excluded.starts_at
            """, nativeQuery = true)
    void chooseMeal(@org.springframework.data.repository.query.Param("userId") Long userId,
                    @org.springframework.data.repository.query.Param("editionId") Long editionId,
                    @org.springframework.data.repository.query.Param("startsAt") String startsAt);

    /** Hand that day's meal back to the scheduler. */
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Query(value = """
            delete from plan_meal m using plan pl
             where m.plan_id = pl.plan_id
               and pl.user_id = :userId and pl.edition_id = :editionId
               and m.meal_on = cast(:onDay as timestamptz)::date
            """, nativeQuery = true)
    void clearMeal(@org.springframework.data.repository.query.Param("userId") Long userId,
                   @org.springframework.data.repository.query.Param("editionId") Long editionId,
                   @org.springframework.data.repository.query.Param("onDay") String onDay);

    /** The days of this plan whose meal the person placed themselves. */
    @org.springframework.data.jpa.repository.Query(value = """
            select m.starts_at::text from plan_meal m join plan pl on pl.plan_id = m.plan_id
             where pl.user_id = :userId and pl.edition_id = :editionId
            """, nativeQuery = true)
    java.util.List<String> chosenMeals(
            @org.springframework.data.repository.query.Param("userId") Long userId,
            @org.springframework.data.repository.query.Param("editionId") Long editionId);

    /**
     * When this person arrives and leaves on one day of one plan.
     *
     * Wall-clock times with no zone, moved as text so Postgres does the only
     * cast — the same precaution as AppUserRepository.paceTimes, and for the
     * same reason: Hibernate converts a bare time by the standard offset and
     * stores something five hours from what was typed.
     *
     * Either end may be left blank. "I arrive at four on Friday" says nothing
     * about when I leave, and a row that says nothing is deleted instead.
     */
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Query(value = """
            insert into plan_day (plan_id, day_on, arrive_at, leave_by)
            select pl.plan_id, cast(:onDay as date),
                   cast(nullif(:arriveAt, '') as time),
                   cast(nullif(:leaveBy, '') as time)
              from plan pl
             where pl.user_id = :userId and pl.edition_id = :editionId
            on conflict (plan_id, day_on) do update
               set arrive_at = excluded.arrive_at,
                   leave_by  = excluded.leave_by,
                   chosen_at = now()
            """, nativeQuery = true)
    void setDayHours(@org.springframework.data.repository.query.Param("userId") Long userId,
                     @org.springframework.data.repository.query.Param("editionId") Long editionId,
                     @org.springframework.data.repository.query.Param("onDay") String onDay,
                     @org.springframework.data.repository.query.Param("arriveAt") String arriveAt,
                     @org.springframework.data.repository.query.Param("leaveBy") String leaveBy);

    /** Hand that day back to the account-wide window. */
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Query(value = """
            delete from plan_day d using plan pl
             where d.plan_id = pl.plan_id
               and pl.user_id = :userId and pl.edition_id = :editionId
               and d.day_on = cast(:onDay as date)
            """, nativeQuery = true)
    void clearDayHours(@org.springframework.data.repository.query.Param("userId") Long userId,
                       @org.springframework.data.repository.query.Param("editionId") Long editionId,
                       @org.springframework.data.repository.query.Param("onDay") String onDay);

    /** The days of this plan with their own hours, as "date|arrive|leave". */
    @org.springframework.data.jpa.repository.Query(value = """
            select d.day_on::text || '|' || coalesce(d.arrive_at::text, '')
                                  || '|' || coalesce(d.leave_by::text, '')
              from plan_day d join plan pl on pl.plan_id = d.plan_id
             where pl.user_id = :userId and pl.edition_id = :editionId
            """, nativeQuery = true)
    java.util.List<String> dayHours(
            @org.springframework.data.repository.query.Param("userId") Long userId,
            @org.springframework.data.repository.query.Param("editionId") Long editionId);

    /** Whether the daily limit should cover the whole day, additions included. */
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.transaction.annotation.Transactional
    @org.springframework.data.jpa.repository.Query(value = """
            update plan set fit_inside_limit = :fit
             where user_id = :userId and edition_id = :editionId
            """, nativeQuery = true)
    void setFitInside(@org.springframework.data.repository.query.Param("userId") Long userId,
                      @org.springframework.data.repository.query.Param("editionId") Long editionId,
                      @org.springframework.data.repository.query.Param("fit") boolean fit);

    @org.springframework.data.jpa.repository.Query(value = """
            select fit_inside_limit from plan
             where user_id = :userId and edition_id = :editionId
            """, nativeQuery = true)
    Boolean fitInside(@org.springframework.data.repository.query.Param("userId") Long userId,
                      @org.springframework.data.repository.query.Param("editionId") Long editionId);
}
