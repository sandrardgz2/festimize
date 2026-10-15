-- Artists for the Sick New World demonstration lineup.
-- Real artists; tags are replaced with MusicBrainz data by db/verify_artists.py.

BEGIN;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Evanescence', 'evanescence', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'evanescence');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'gothic metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='evanescence' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='evanescence' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='evanescence' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'female vocals', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='evanescence' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'symphonic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='evanescence' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '2000s', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='evanescence' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Bring Me the Horizon', 'bring me the horizon', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'bring me the horizon');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='bring me the horizon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='bring me the horizon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'electronic rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='bring me the horizon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='bring me the horizon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'experimental', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='bring me the horizon' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Underoath', 'underoath', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'underoath');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='underoath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='underoath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='underoath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '2000s', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='underoath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'emotional', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='underoath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'screamo', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='underoath' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'AFI', 'afi', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'afi');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'punk rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='afi' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='afi' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'gothic rock', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='afi' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='afi' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='afi' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'anthemic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='afi' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Ministry', 'ministry', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'ministry');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'industrial metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='ministry' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'industrial rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='ministry' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='ministry' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'political', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='ministry' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'classic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='ministry' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'electronic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='ministry' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'The Prodigy', 'the prodigy', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'the prodigy');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'big beat', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='the prodigy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'electronic', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='the prodigy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'breakbeat', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='the prodigy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='the prodigy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'dance', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='the prodigy' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'rave', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='the prodigy' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Mudvayne', 'mudvayne', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'mudvayne');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='mudvayne' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='mudvayne' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='mudvayne' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'technical', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='mudvayne' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '2000s', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='mudvayne' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Static-X', 'static-x', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'static-x');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'industrial metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='static-x' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='static-x' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'electronic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='static-x' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='static-x' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='static-x' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '2000s', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='static-x' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Hatebreed', 'hatebreed', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'hatebreed');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metallic hardcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='hatebreed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='hatebreed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='hatebreed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'beatdown', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='hatebreed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'anthemic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='hatebreed' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Sevendust', 'sevendust', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'sevendust');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='sevendust' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='sevendust' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='sevendust' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='sevendust' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '2000s', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='sevendust' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Chevelle', 'chevelle', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'chevelle');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='chevelle' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-grunge', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='chevelle' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='chevelle' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'radio rock', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='chevelle' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '2000s', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='chevelle' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Acid Bath', 'acid bath', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'acid bath');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludge metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='acid bath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'doom metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized='acid bath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'southern', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized='acid bath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'dark', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized='acid bath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'cult', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized='acid bath' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized='acid bath' ON CONFLICT DO NOTHING;

COMMIT;
