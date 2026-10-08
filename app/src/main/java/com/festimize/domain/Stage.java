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

/** Maps dim_stage. */
@Entity
@Table(name = "dim_stage",
        uniqueConstraints = @UniqueConstraint(columnNames = {"festival_id", "name"}))
public class Stage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "stage_id")
    private Long stageId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "festival_id", nullable = false)
    private Festival festival;

    @Column(name = "name", nullable = false)
    private String name;

    /** 1 = main stage. Drives the rising-artist measure. */
    @Column(name = "size_rank")
    private Short sizeRank;

    public Long getStageId() {
        return stageId;
    }

    public void setStageId(Long stageId) {
        this.stageId = stageId;
    }

    public Festival getFestival() {
        return festival;
    }

    public void setFestival(Festival festival) {
        this.festival = festival;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Short getSizeRank() {
        return sizeRank;
    }

    public void setSizeRank(Short sizeRank) {
        this.sizeRank = sizeRank;
    }
}
