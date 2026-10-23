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
}
