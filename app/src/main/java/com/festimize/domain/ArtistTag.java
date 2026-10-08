package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;

/** Maps artist_tag. Tags are the basis of taste matching, so weight and source both matter. */
@Entity
@Table(name = "artist_tag")
@IdClass(ArtistTagId.class)
public class ArtistTag {

    @Id
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "artist_id", nullable = false)
    private Artist artist;

    @Id
    @Column(name = "tag", nullable = false)
    private String tag;

    /** 'musicbrainz' | 'lastfm' */
    @Id
    @Column(name = "source", nullable = false)
    private String source;

    /** Last.fm count, or 1 for MusicBrainz genres. */
    @Column(name = "weight", nullable = false, precision = 6, scale = 3)
    private BigDecimal weight = BigDecimal.ONE;

    public Artist getArtist() {
        return artist;
    }

    public void setArtist(Artist artist) {
        this.artist = artist;
    }

    public String getTag() {
        return tag;
    }

    public void setTag(String tag) {
        this.tag = tag;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public BigDecimal getWeight() {
        return weight;
    }

    public void setWeight(BigDecimal weight) {
        this.weight = weight;
    }
}
