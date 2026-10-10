-- Additional artists for the Steel City Open Air demonstration lineup.
-- Real artists; tags are replaced with MusicBrainz data by db/verify_artists.py.

BEGIN;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Spiritbox', 'spiritbox', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'spiritbox');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'djent', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'clean and harsh vocals', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'canadian', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'spiritbox' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Bad Omens', 'bad omens', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'bad omens');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'electronic rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'bad omens' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Architects', 'architects', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'architects');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'british', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'anthemic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'architects' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Parkway Drive', 'parkway drive', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'parkway drive');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'australian', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'anthemic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'parkway drive' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Jinjer', 'jinjer', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'jinjer');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'ukrainian', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'technical', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'clean and harsh vocals', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'jinjer' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Whitechapel', 'whitechapel', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'whitechapel');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'deathcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'technical death metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'brutal', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'whitechapel' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Fit for an Autopsy', 'fit for an autopsy', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'fit for an autopsy');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'deathcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'fit for an autopsy' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Thy Art Is Murder', 'thy art is murder', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'thy art is murder');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'deathcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'death metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'australian', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'brutal', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'thy art is murder' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Northlane', 'northlane', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'northlane');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'electronic metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'australian', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'djent', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'northlane' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Polaris', 'polaris', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'polaris');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'australian', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'emotional', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'polaris' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Erra', 'erra', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'erra');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'djent', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'technical', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'erra' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Currents', 'currents', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'currents');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'djent', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'emotional', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'currents' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Silent Planet', 'silent planet', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'silent planet');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'lyrical', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'silent planet' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Vein.fm', 'vein.fm', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'vein.fm');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'mathcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'chaotic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'vein.fm' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Harm''s Way', 'harm''s way', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'harm''s way');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metallic hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'industrial', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'harm''s way' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Jesus Piece', 'jesus piece', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'jesus piece');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metallic hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'jesus piece' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Scowl', 'scowl', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'scowl');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'energetic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'crossover', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'scowl' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Drain', 'drain', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'drain');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'crossover thrash', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'energetic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'fun', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'drain' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Zulu', 'zulu', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'zulu');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'powerviolence', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'soul samples', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'short songs', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'zulu' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Static Dress', 'static dress', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'static dress');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'emo', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'british', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'chaotic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nostalgic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'static dress' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Vended', 'vended', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'vended');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'vended' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Boundaries', 'boundaries', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'boundaries');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metallic hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'beatdown', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'boundaries' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Sanguisugabogg', 'sanguisugabogg', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'sanguisugabogg');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'death metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'slam', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'brutal', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'sanguisugabogg' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Dying Wish', 'dying wish', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'dying wish');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'emotional', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'dying wish' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Kublai Khan TX', 'kublai khan tx', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'kublai khan tx');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'beatdown hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metallic hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'kublai khan tx' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Bodysnatcher', 'bodysnatcher', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'bodysnatcher');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'deathcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'beatdown hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'american', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'modern', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'brutal', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'bodysnatcher' ON CONFLICT DO NOTHING;

COMMIT;
