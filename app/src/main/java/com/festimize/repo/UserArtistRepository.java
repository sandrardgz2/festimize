package com.festimize.repo;

import com.festimize.domain.Artist;
import com.festimize.domain.UserArtist;
import com.festimize.domain.UserArtistId;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
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
}
