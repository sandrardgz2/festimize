package com.festimize.domain;

import java.io.Serializable;
import java.util.Objects;

/** Composite key for user_artist: (user_id, artist_id). */
public class UserArtistId implements Serializable {

    private Long user;
    private Long artist;

    public UserArtistId() {
    }

    public UserArtistId(Long user, Long artist) {
        this.user = user;
        this.artist = artist;
    }

    public Long getUser() {
        return user;
    }

    public void setUser(Long user) {
        this.user = user;
    }

    public Long getArtist() {
        return artist;
    }

    public void setArtist(Long artist) {
        this.artist = artist;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof UserArtistId other)) {
            return false;
        }
        return Objects.equals(user, other.user) && Objects.equals(artist, other.artist);
    }

    @Override
    public int hashCode() {
        return Objects.hash(user, artist);
    }
}
