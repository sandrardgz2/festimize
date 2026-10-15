package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.MapsId;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import org.hibernate.annotations.CreationTimestamp;

/** Maps artist_momentum — the rising measure, one row per artist, recomputed in batch. */
@Entity
@Table(name = "artist_momentum")
public class ArtistMomentum {

    @Id
    @Column(name = "artist_id")
    private Long artistId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "artist_id", nullable = false)
    private Artist artist;

    @Column(name = "momentum_score", nullable = false, precision = 5, scale = 4)
    private BigDecimal momentumScore;

    @Column(name = "appearances", nullable = false)
    private Short appearances;

    @Column(name = "first_year")
    private Short firstYear;

    @Column(name = "last_year")
    private Short lastYear;

    /**
     * How many different festivals, which is not the same as how many
     * appearances: two Belgian festivals every year is a residency, and three
     * is the least a rising badge will accept.
     */
    @Column(name = "festivals")
    private Short festivals;

    /**
     * Which case produced the score, because the three mean different things
     * on a page: {@code trajectory} is a measured climb over three or more
     * years, {@code returning} is the same climb by an artist who has been
     * going for decades, {@code new} is too little history to say anything —
     * and the page shows the facts instead — and {@code arrived} is an artist
     * already at the top of the circuit, who is excluded on purpose.
     */
    @Column(name = "basis", nullable = false)
    private String basis;

    @CreationTimestamp
    @Column(name = "computed_at", nullable = false)
    private OffsetDateTime computedAt;

    public Long getArtistId() {
        return artistId;
    }

    public void setArtistId(Long artistId) {
        this.artistId = artistId;
    }

    public Artist getArtist() {
        return artist;
    }

    public void setArtist(Artist artist) {
        this.artist = artist;
    }

    public BigDecimal getMomentumScore() {
        return momentumScore;
    }

    public void setMomentumScore(BigDecimal momentumScore) {
        this.momentumScore = momentumScore;
    }

    public Short getAppearances() {
        return appearances;
    }

    public void setAppearances(Short appearances) {
        this.appearances = appearances;
    }

    public Short getFirstYear() {
        return firstYear;
    }

    public void setFirstYear(Short firstYear) {
        this.firstYear = firstYear;
    }

    public Short getFestivals() {
        return festivals;
    }

    public void setFestivals(Short festivals) {
        this.festivals = festivals;
    }

    public String getBasis() {
        return basis;
    }

    public void setBasis(String basis) {
        this.basis = basis;
    }

    /** Whether this artist has earned a rising badge, by the one rule. */
    public boolean isRising() {
        return "trajectory".equals(basis)
                && festivals != null && festivals >= 3
                && momentumScore != null
                && momentumScore.compareTo(new BigDecimal("0.75")) >= 0;
    }

    public Short getLastYear() {
        return lastYear;
    }

    public void setLastYear(Short lastYear) {
        this.lastYear = lastYear;
    }

    public OffsetDateTime getComputedAt() {
        return computedAt;
    }

    public void setComputedAt(OffsetDateTime computedAt) {
        this.computedAt = computedAt;
    }
}
