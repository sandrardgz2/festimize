package com.festimize.repo;

import com.festimize.domain.FestivalEdition;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface FestivalEditionRepository extends JpaRepository<FestivalEdition, Long> {

    List<FestivalEdition> findByFestival_FestivalIdOrderByYearDesc(Long festivalId);

    Optional<FestivalEdition> findByFestival_FestivalIdAndYear(Long festivalId, Short year);

    /** Editions with their festival already loaded — open-in-view is off, so lazy proxies fail in the view. */
    @Query("select e from FestivalEdition e join fetch e.festival f order by f.name asc, e.year desc")
    List<FestivalEdition> findAllWithFestival();
}
