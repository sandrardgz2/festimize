package com.festimize.repo;

import com.festimize.domain.ArtistTag;
import com.festimize.domain.ArtistTagId;
import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ArtistTagRepository extends JpaRepository<ArtistTag, ArtistTagId> {

    List<ArtistTag> findByArtist_ArtistId(Long artistId);

    /** Tags for a batch of artists, so a lineup page is one query rather than one per artist. */
    @Query("select t from ArtistTag t where t.artist.artistId in :artistIds order by t.weight desc")
    List<ArtistTag> findForArtists(@Param("artistIds") Collection<Long> artistIds);
}
