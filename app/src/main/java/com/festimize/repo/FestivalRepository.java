package com.festimize.repo;

import com.festimize.domain.Festival;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FestivalRepository extends JpaRepository<Festival, Long> {

    List<Festival> findAllByOrderByNameAsc();
}
