package com.festimize.repo;

import com.festimize.domain.Artist;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ArtistRepository extends JpaRepository<Artist, Long> {

    Optional<Artist> findByMbid(UUID mbid);

    List<Artist> findByNameNormalizedStartingWithOrderByNameAsc(String prefix);

    /**
     * Artists whose name contains this text, best guesses first.
     *
     * A prefix match was there already and is not what a search box needs:
     * somebody looking for "Knocked Loose" may well type "loose". Names that
     * start with the text still sort first, because they are usually what was
     * meant.
     */
    @org.springframework.data.jpa.repository.Query("""
            select a from Artist a
            where lower(a.name) like concat('%', lower(:text), '%')
            order by case when lower(a.name) like concat(lower(:text), '%') then 0 else 1 end,
                     length(a.name), a.name
            """)
    List<Artist> search(@org.springframework.data.repository.query.Param("text") String text,
                        org.springframework.data.domain.Pageable limit);
}
