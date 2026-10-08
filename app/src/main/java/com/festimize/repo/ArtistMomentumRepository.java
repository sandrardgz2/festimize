package com.festimize.repo;

import com.festimize.domain.ArtistMomentum;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ArtistMomentumRepository extends JpaRepository<ArtistMomentum, Long> {

    List<ArtistMomentum> findByArtistIdIn(List<Long> artistIds);
}
