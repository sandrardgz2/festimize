package com.festimize.repo;

import com.festimize.domain.PlanItem;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PlanItemRepository extends JpaRepository<PlanItem, Long> {

    List<PlanItem> findByPlan_PlanIdOrderByStartsAtAsc(Long planId);
}
