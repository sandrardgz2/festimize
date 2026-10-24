package com.festimize.repo;

import com.festimize.domain.Artist;
import com.festimize.domain.UserArtist;
import com.festimize.domain.UserArtistId;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface UserArtistRepository extends JpaRepository<UserArtist, UserArtistId> {

    List<UserArtist> findByUser_UserIdOrderByAddedAtAsc(Long userId);

    /** The artists one person has saved, oldest pick first. */
    @Query("""
            select ua.artist from UserArtist ua
            where ua.user.userId = :userId
            order by ua.addedAt asc
            """)
    List<Artist> findSavedArtists(@Param("userId") Long userId);

    /**
     * The artist ids this person marked must-see.
     *
     * A projection rather than the entities: open-in-view is off, so reading
     * ua.getArtist() outside the transaction throws, and this is read on
     * every setup render.
     */
    @Query("""
            select ua.artist.artistId from UserArtist ua
            where ua.user.userId = :userId and ua.mustSee = true
            """)
    List<Long> mustSeeArtistIds(@Param("userId") Long userId);

    @Modifying
    @Query("""
            update UserArtist ua set ua.mustSee = :on
            where ua.user.userId = :userId and ua.artist.artistId = :artistId
            """)
    int setMustSee(@Param("userId") Long userId, @Param("artistId") Long artistId,
                   @Param("on") boolean on);
}
