package com.festimize.repo;

import com.festimize.domain.Plan;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PlanRepository extends JpaRepository<Plan, Long> {

    long countByUser_UserId(Long userId);

    Optional<Plan> findByUser_UserIdAndEdition_EditionId(Long userId, Long editionId);

    List<Plan> findByUser_UserIdOrderByUpdatedAtDesc(Long userId);
}
