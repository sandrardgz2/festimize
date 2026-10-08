package com.festimize.repo;

import com.festimize.domain.Stage;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StageRepository extends JpaRepository<Stage, Long> {

    List<Stage> findByFestival_FestivalIdOrderBySizeRankAscNameAsc(Long festivalId);
}
