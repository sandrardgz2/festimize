package com.festimize.repo;

import com.festimize.domain.ArtistMomentum;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ArtistMomentumRepository extends JpaRepository<ArtistMomentum, Long> {

    List<ArtistMomentum> findByArtistIdIn(List<Long> artistIds);

    Optional<ArtistMomentum> findByArtistId(Long artistId);

    /**
     * The artists climbing fastest, for the discovery list.
     *
     * The three conditions are the badge's definition and each one was put
     * there by a bad answer: a trajectory needs three years of history, three
     * different festivals rule out a residency at two neighbouring ones, and
     * the score threshold keeps it to the strongest quarter. Why those and not
     * something else is in docs/evaluation/momentum-backtest.md.
     */
    @Query("""
            select m from ArtistMomentum m
            join fetch m.artist a
            where m.basis = 'trajectory'
              and m.festivals >= 3
              and m.momentumScore >= 0.75
            order by m.momentumScore desc
            """)
    List<ArtistMomentum> findRising();

    /** One artist's measure plus every artist they have shared a bill with. */
    @Query("""
            select m from ArtistMomentum m
            join fetch m.artist a
            where a.artistId in :artistIds
            """)
    List<ArtistMomentum> findForArtists(@Param("artistIds") List<Long> artistIds);
}
