package com.festimize.repo;

import com.festimize.domain.Artist;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ArtistRepository extends JpaRepository<Artist, Long> {

    Optional<Artist> findByMbid(UUID mbid);

    List<Artist> findByNameNormalizedStartingWithOrderByNameAsc(String prefix);
}
