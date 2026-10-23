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
