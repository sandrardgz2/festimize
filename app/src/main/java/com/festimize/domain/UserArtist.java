package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import org.hibernate.annotations.CreationTimestamp;

/**
 * Maps user_artist — the artists someone named as theirs.
 * Taste lives on the account, never on a plan: that is what makes switching festivals cheap.
 */
@Entity
@Table(name = "user_artist")
@IdClass(UserArtistId.class)
public class UserArtist {

    @Id
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private AppUser user;

    @Id
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "artist_id", nullable = false)
    private Artist artist;

    @CreationTimestamp
    @Column(name = "added_at", nullable = false, updatable = false)
    private OffsetDateTime addedAt;

    /**
     * The person came for this one.
     *
     * Saved artists all weighed the same, so a clash between two of them was
     * settled on match score. This is the only place the difference between
     * "I came for this band" and "I would like to catch them" is recorded.
     */
    @Column(name = "must_see", nullable = false)
    private boolean mustSee;

    public AppUser getUser() {
        return user;
    }

    public void setUser(AppUser user) {
        this.user = user;
    }

    public Artist getArtist() {
        return artist;
    }

    public void setArtist(Artist artist) {
        this.artist = artist;
    }

    public boolean isMustSee() {
        return mustSee;
    }

    public void setMustSee(boolean mustSee) {
        this.mustSee = mustSee;
    }

    public OffsetDateTime getAddedAt() {
        return addedAt;
    }

    public void setAddedAt(OffsetDateTime addedAt) {
        this.addedAt = addedAt;
    }
}
