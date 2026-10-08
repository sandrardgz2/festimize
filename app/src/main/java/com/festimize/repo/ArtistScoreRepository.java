package com.festimize.repo;

import com.festimize.domain.ArtistScore;
import com.festimize.domain.ArtistScoreId;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ArtistScoreRepository extends JpaRepository<ArtistScore, ArtistScoreId> {

    List<ArtistScore> findByUser_UserIdOrderByMatchScoreDesc(Long userId);
}
