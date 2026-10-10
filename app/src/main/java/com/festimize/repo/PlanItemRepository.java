package com.festimize.repo;

import com.festimize.domain.PlanItem;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PlanItemRepository extends JpaRepository<PlanItem, Long> {

    List<PlanItem> findByPlan_PlanIdOrderByStartsAtAsc(Long planId);

    /**
     * Plan items with the performance, artist and stage already loaded.
     * open-in-view is off, so anything the template touches must be fetched here.
     */
    @Query("""
            select i from PlanItem i
            left join fetch i.performance p
            left join fetch p.artist
            left join fetch p.stage
            where i.plan.planId = :planId
            order by i.startsAt asc
            """)
    List<PlanItem> findForPlan(@Param("planId") Long planId);
}
