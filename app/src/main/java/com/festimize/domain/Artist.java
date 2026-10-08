package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import java.util.UUID;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/** Maps dim_artist. */
@Entity
@Table(name = "dim_artist")
public class Artist {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "artist_id")
    private Long artistId;

    /** MusicBrainz id — the canonical key. */
    @Column(name = "mbid", unique = true)
    private UUID mbid;

    @Column(name = "name", nullable = false)
    private String name;

    /** Lowercased, punctuation stripped, for matching. */
    @Column(name = "name_normalized", nullable = false)
    private String nameNormalized;

    @Column(name = "disambiguation")
    private String disambiguation;

    // char(2) in Postgres reports as CHAR, not VARCHAR — say so or ddl-auto=validate fails.
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "country", length = 2, columnDefinition = "char(2)")
    private String country;

    @Column(name = "formed_year")
    private Short formedYear;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    public Long getArtistId() {
        return artistId;
    }

    public void setArtistId(Long artistId) {
        this.artistId = artistId;
    }

    public UUID getMbid() {
        return mbid;
    }

    public void setMbid(UUID mbid) {
        this.mbid = mbid;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getNameNormalized() {
        return nameNormalized;
    }

    public void setNameNormalized(String nameNormalized) {
        this.nameNormalized = nameNormalized;
    }

    public String getDisambiguation() {
        return disambiguation;
    }

    public void setDisambiguation(String disambiguation) {
        this.disambiguation = disambiguation;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public Short getFormedYear() {
        return formedYear;
    }

    public void setFormedYear(Short formedYear) {
        this.formedYear = formedYear;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
