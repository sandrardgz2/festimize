package com.festimize.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/** Maps dim_festival. */
@Entity
@Table(name = "dim_festival",
        uniqueConstraints = @UniqueConstraint(columnNames = {"name", "country"}))
public class Festival {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "festival_id")
    private Long festivalId;

    @Column(name = "name", nullable = false)
    private String name;

    // char(2) in Postgres reports as CHAR, not VARCHAR — say so or ddl-auto=validate fails.
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "country", length = 2, columnDefinition = "char(2)")
    private String country;

    @Column(name = "city")
    private String city;

    @Column(name = "website")
    private String website;

    public Long getFestivalId() {
        return festivalId;
    }

    public void setFestivalId(Long festivalId) {
        this.festivalId = festivalId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getWebsite() {
        return website;
    }

    public void setWebsite(String website) {
        this.website = website;
    }
}
