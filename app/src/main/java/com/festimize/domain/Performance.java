package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.math.BigDecimal;
import java.time.OffsetDateTime;

/**
 * Maps fact_performance — one artist playing one festival edition.
 * Historical rows have no set times; demo festivals are entered by hand and do.
 */
@Entity
@Table(name = "fact_performance",
        uniqueConstraints = @UniqueConstraint(
                columnNames = {"artist_id", "edition_id", "stage_id", "starts_at"}))
public class Performance {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "performance_id")
    private Long performanceId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "artist_id", nullable = false)
    private Artist artist;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "edition_id", nullable = false)
    private FestivalEdition edition;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "stage_id")
    private Stage stage;

    /** FK to dim_date (yyyymmdd). dim_date is analytics-only, so it is kept as a plain value. */
    @Column(name = "date_id")
    private Integer dateId;

    @Column(name = "starts_at")
    private OffsetDateTime startsAt;

    @Column(name = "ends_at")
    private OffsetDateTime endsAt;

    /** Position on the poster, 1 = top. */
    @Column(name = "billing_rank")
    private Short billingRank;

    @Column(name = "is_headliner", nullable = false)
    private boolean headliner = false;

    /** 'wikipedia' | 'wikidata' | 'manual' */
    @Column(name = "source", nullable = false)
    private String source;

    /** Below 1 = flagged for review. */
    @Column(name = "confidence", nullable = false, precision = 3, scale = 2)
    private BigDecimal confidence = BigDecimal.ONE;

    public Long getPerformanceId() {
        return performanceId;
    }

    public void setPerformanceId(Long performanceId) {
        this.performanceId = performanceId;
    }

    public Artist getArtist() {
        return artist;
    }

    public void setArtist(Artist artist) {
        this.artist = artist;
    }

    public FestivalEdition getEdition() {
        return edition;
    }

    public void setEdition(FestivalEdition edition) {
        this.edition = edition;
    }

    public Stage getStage() {
        return stage;
    }

    public void setStage(Stage stage) {
        this.stage = stage;
    }

    public Integer getDateId() {
        return dateId;
    }

    public void setDateId(Integer dateId) {
        this.dateId = dateId;
    }

    public OffsetDateTime getStartsAt() {
        return startsAt;
    }

    public void setStartsAt(OffsetDateTime startsAt) {
        this.startsAt = startsAt;
    }

    public OffsetDateTime getEndsAt() {
        return endsAt;
    }

    public void setEndsAt(OffsetDateTime endsAt) {
        this.endsAt = endsAt;
    }

    public Short getBillingRank() {
        return billingRank;
    }

    public void setBillingRank(Short billingRank) {
        this.billingRank = billingRank;
    }

    public boolean isHeadliner() {
        return headliner;
    }

    public void setHeadliner(boolean headliner) {
        this.headliner = headliner;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public void setConfidence(BigDecimal confidence) {
        this.confidence = confidence;
    }
}
