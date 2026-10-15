package com.festimize.repo;

import com.festimize.domain.Performance;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

/**
 * One artist's festival history, which is a different question from a
 * festival's lineup and so a different repository.
 */
public interface ArtistHistoryRepository extends JpaRepository<Performance, Long> {

    /**
     * Every festival this artist has played, most recent first.
     *
     * Cancelled editions come back too, flagged on the edition, because an
     * announced booking is a real fact about who was hired even though nobody
     * played it. The page says which is which; the measure ignores them.
     */
    @Query("""
            select p from Performance p
            join fetch p.edition e
            join fetch e.festival f
            left join fetch p.stage s
            where p.artist.artistId = :artistId
            order by e.year desc, f.name asc
            """)
    List<Performance> findHistory(@Param("artistId") Long artistId);
}
