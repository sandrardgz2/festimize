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
}
