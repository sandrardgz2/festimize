package com.festimize.domain;

import java.io.Serializable;
import java.util.Objects;

/** Composite key for artist_tag: (artist_id, tag, source). */
public class ArtistTagId implements Serializable {

    private Long artist;
    private String tag;
    private String source;

    public ArtistTagId() {
    }

    public ArtistTagId(Long artist, String tag, String source) {
        this.artist = artist;
        this.tag = tag;
        this.source = source;
    }

    public Long getArtist() {
        return artist;
    }

    public void setArtist(Long artist) {
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

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof ArtistTagId other)) {
            return false;
        }
        return Objects.equals(artist, other.artist)
                && Objects.equals(tag, other.tag)
                && Objects.equals(source, other.source);
    }

    @Override
    public int hashCode() {
        return Objects.hash(artist, tag, source);
    }
}
