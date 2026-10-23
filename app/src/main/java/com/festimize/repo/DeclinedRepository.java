package com.festimize.repo;

import com.festimize.domain.Plan;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

/**
 * Sets turned down on one plan.
 *
 * Native statements against a join table with no entity of its own: it holds
 * two foreign keys and a timestamp, and giving it an entity would be more
 * mapping than the thing is worth.
 */
public interface DeclinedRepository extends JpaRepository<Plan, Long> {

    @Modifying
    @Transactional
    @Query(value = """
            insert into plan_declined (plan_id, performance_id)
            select pl.plan_id, :performanceId from plan pl
             where pl.user_id = :userId and pl.edition_id = :editionId
            on conflict do nothing
            """, nativeQuery = true)
    void decline(@Param("userId") Long userId, @Param("editionId") Long editionId,
                 @Param("performanceId") Long performanceId);

    /** Everything comes back, which is how someone undoes a decision they regret. */
    @Modifying
    @Transactional
    @Query(value = """
            delete from plan_declined d using plan pl
             where d.plan_id = pl.plan_id
               and pl.user_id = :userId and pl.edition_id = :editionId
            """, nativeQuery = true)
    void restoreAll(@Param("userId") Long userId, @Param("editionId") Long editionId);

    @Query(value = """
            select count(*) from plan_declined d join plan pl on pl.plan_id = d.plan_id
             where pl.user_id = :userId and pl.edition_id = :editionId
            """, nativeQuery = true)
    long countFor(@Param("userId") Long userId, @Param("editionId") Long editionId);

    /**
     * Ask for one artist by name. Dropping a set frees its slot and lets the
     * solver decide what fills it; pinning says which act should have it.
     */
    @Modifying
    @Transactional
    @Query(value = """
            insert into plan_pinned (plan_id, performance_id)
            select pl.plan_id, :performanceId from plan pl
             where pl.user_id = :userId and pl.edition_id = :editionId
            on conflict do nothing
            """, nativeQuery = true)
    void pin(@Param("userId") Long userId, @Param("editionId") Long editionId,
             @Param("performanceId") Long performanceId);

    @Modifying
    @Transactional
    @Query(value = """
            delete from plan_pinned p using plan pl
             where p.plan_id = pl.plan_id
               and pl.user_id = :userId and pl.edition_id = :editionId
            """, nativeQuery = true)
    void unpinAll(@Param("userId") Long userId, @Param("editionId") Long editionId);

    /**
     * Lift any pin that clashes with the set about to be pinned.
     *
     * Two pinned sets at the same hour are a contradiction the scheduler
     * cannot honour, and the way one arises is ordinary: ask for Currents
     * over Slipknot, then change your mind. Without this the second request
     * was added to the first rather than replacing it. The ten minutes match
     * the scheduler's changeover, so a pin displaces exactly what it would
     * have displaced there.
     */
    @Modifying
    @Transactional
    @Query(value = """
            delete from plan_pinned p
             using plan pl, fact_performance mine, fact_performance theirs
             where p.plan_id = pl.plan_id
               and pl.user_id = :userId and pl.edition_id = :editionId
               and mine.performance_id = :performanceId
               and theirs.performance_id = p.performance_id
               and theirs.performance_id <> mine.performance_id
               and theirs.starts_at < mine.ends_at + interval '10 minutes'
               and theirs.ends_at + interval '10 minutes' > mine.starts_at
            """, nativeQuery = true)
    void unpinClashing(@Param("userId") Long userId, @Param("editionId") Long editionId,
                       @Param("performanceId") Long performanceId);

    /**
     * Asking for a set by name undoes having turned it down. A declined set is
     * filtered out before the scheduler sees it, so pinning one without this
     * is a button that does nothing.
     */
    @Modifying
    @Transactional
    @Query(value = """
            delete from plan_declined d using plan pl
             where d.plan_id = pl.plan_id
               and pl.user_id = :userId and pl.edition_id = :editionId
               and d.performance_id = :performanceId
            """, nativeQuery = true)
    void undecline(@Param("userId") Long userId, @Param("editionId") Long editionId,
                   @Param("performanceId") Long performanceId);

    @Query(value = """
            select count(*) from plan_pinned p join plan pl on pl.plan_id = p.plan_id
             where pl.user_id = :userId and pl.edition_id = :editionId
            """, nativeQuery = true)
    long pinnedFor(@Param("userId") Long userId, @Param("editionId") Long editionId);

    /**
     * Pin only the part of a set that falls inside a gap.
     *
     * The ordinary pin takes the whole set, which is right when somebody
     * asks for an artist and wrong when the page has just told them that 40
     * of 60 minutes fall in this gap: accepting that offer used to remove
     * whatever the other 20 minutes clashed with, which on the account it
     * was found on was one of their own picks. A window keeps the clash out
     * of the day, so nothing is displaced.
     */
    @Modifying
    @Transactional
    @Query(value = """
            insert into plan_pinned (plan_id, performance_id, from_at, to_at)
            select pl.plan_id, :performanceId, :fromAt, :toAt from plan pl
             where pl.user_id = :userId and pl.edition_id = :editionId
            on conflict (plan_id, performance_id)
            do update set from_at = excluded.from_at, to_at = excluded.to_at
            """, nativeQuery = true)
    void pinWindow(@Param("userId") Long userId, @Param("editionId") Long editionId,
                   @Param("performanceId") Long performanceId,
                   @Param("fromAt") java.time.OffsetDateTime fromAt,
                   @Param("toAt") java.time.OffsetDateTime toAt);
}
