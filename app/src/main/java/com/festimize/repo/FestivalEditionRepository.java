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

    /**
     * The editions a schedule can be built for: the ones with set times.
     *
     * A schedule is a plan for a day, so it needs times, and the historical
     * lineups read from articles and setlists have none. Before the corpus was
     * loaded there were three editions in the database and every page could
     * safely list all of them; afterwards there were 334, and both the lineup
     * and schedule pages offered every one of them as something to plan.
     */
    @Query("""
            select e from FestivalEdition e
            join fetch e.festival f
            where exists (select 1 from Performance p
                           where p.edition = e and p.startsAt is not null)
            order by f.name asc, e.year desc
            """)
    List<FestivalEdition> findPlannable();
}
