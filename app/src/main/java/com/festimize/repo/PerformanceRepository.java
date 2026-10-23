package com.festimize.repo;

import com.festimize.domain.Performance;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PerformanceRepository extends JpaRepository<Performance, Long> {

    /**
     * Every performance at one festival edition, earliest set first.
     * Historical rows have a null starts_at, so they sort last.
     */
    @Query("""
            select p from Performance p
            join fetch p.artist a
            left join fetch p.stage s
            where p.edition.editionId = :editionId
            order by p.startsAt asc nulls last, a.name asc
            """)
    List<Performance> findForEditionOrderedByStart(@Param("editionId") Long editionId);

    /**
     * The artist's name for one performance, as a string.
     *
     * A findById here hands back a Performance whose artist is a lazy proxy,
     * and open-in-view is off, so reading the name off it outside a
     * transaction throws. The path expression makes the join explicit and
     * returns the name itself.
     */
    @org.springframework.data.jpa.repository.Query(
            "select p.artist.name from Performance p where p.performanceId = :id")
    java.util.Optional<String> artistNameFor(
            @org.springframework.data.repository.query.Param("id") Long id);
}
