-- Additional artists for taste selection (United States).
-- These are real artists with plausible descriptive tags. They are here so the setup page
-- offers recognisable names beyond one festival's lineup: a taste profile is not limited to
-- who happens to be playing. No performances are created for them.

BEGIN;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Metallica', 'metallica', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'metallica');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'thrash metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'metallica' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'metallica' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'bay area thrash', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'metallica' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'arena metal', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'metallica' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'classic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'metallica' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'metallica' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Slayer', 'slayer', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'slayer');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'thrash metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'slayer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'speed metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'slayer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'slayer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'classic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'slayer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'dark', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'slayer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'slayer' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Pantera', 'pantera', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'pantera');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'pantera' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'thrash metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'pantera' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'southern metal', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'pantera' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'classic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'pantera' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'pantera' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Tool', 'tool', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'tool');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'tool' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'tool' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'psychedelic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'tool' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'odd time signatures', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'tool' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'tool' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'cerebral', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'tool' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'System of a Down', 'system of a down', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'system of a down');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'system of a down' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'system of a down' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'political', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'system of a down' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'eclectic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'system of a down' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'system of a down' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'system of a down' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Korn', 'korn', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'korn');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'korn' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'korn' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'downtuned', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'korn' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'korn' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'korn' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'angsty', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'korn' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Deftones', 'deftones', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'deftones');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'deftones' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'shoegaze', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'deftones' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'dream pop', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'deftones' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'deftones' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'deftones' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Slipknot', 'slipknot', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'slipknot');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'slipknot' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'slipknot' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'slipknot' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'percussive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'slipknot' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'masked', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'slipknot' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Lamb of God', 'lamb of god', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'lamb of god');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'lamb of god' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'lamb of god' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'lamb of god' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'lamb of god' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Mastodon', 'mastodon', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'mastodon');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'mastodon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludge metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'mastodon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'psychedelic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'mastodon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'technical', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'mastodon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'mastodon' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'concept albums', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'mastodon' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Avenged Sevenfold', 'avenged sevenfold', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'avenged sevenfold');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'avenged sevenfold' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hard rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'avenged sevenfold' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'avenged sevenfold' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'guitar solos', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'avenged sevenfold' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'arena metal', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'avenged sevenfold' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Disturbed', 'disturbed', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'disturbed');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'disturbed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nu metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'disturbed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'arena metal', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'disturbed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'radio rock', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'disturbed' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'disturbed' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Alice in Chains', 'alice in chains', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'alice in chains');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'grunge', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'alice in chains' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'alice in chains' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'alice in chains' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'harmony vocals', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'alice in chains' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'dark', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'alice in chains' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludgy', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'alice in chains' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Soundgarden', 'soundgarden', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'soundgarden');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'grunge', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'soundgarden' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'soundgarden' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'soundgarden' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'psychedelic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'soundgarden' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'soundgarden' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Nirvana', 'nirvana', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'nirvana');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'grunge', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'nirvana' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'nirvana' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'nirvana' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'punk', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'nirvana' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'raw', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'nirvana' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'nirvana' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Foo Fighters', 'foo fighters', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'foo fighters');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'foo fighters' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-grunge', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'foo fighters' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'arena rock', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'foo fighters' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'foo fighters' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'radio rock', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'foo fighters' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'foo fighters' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Rage Against the Machine', 'rage against the machine', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'rage against the machine');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'rap metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'rage against the machine' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'rage against the machine' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'political', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'rage against the machine' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'funk metal', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'rage against the machine' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, '90s', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'rage against the machine' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'rage against the machine' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Queens of the Stone Age', 'queens of the stone age', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'queens of the stone age');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'stoner rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'queens of the stone age' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'desert rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'queens of the stone age' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'queens of the stone age' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'queens of the stone age' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'psychedelic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'queens of the stone age' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'queens of the stone age' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Red Fang', 'red fang', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'red fang');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'stoner rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'red fang' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludge metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'red fang' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'red fang' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'fuzz', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'red fang' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'party', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'red fang' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'High on Fire', 'high on fire', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'high on fire');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludge metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'high on fire' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'stoner metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'high on fire' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'thrash', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'high on fire' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'high on fire' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'high on fire' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Sleep', 'sleep', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'sleep');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'doom metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'sleep' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'stoner metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'sleep' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'sleep' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'psychedelic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'sleep' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'slow', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'sleep' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'weed', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'sleep' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Baroness', 'baroness', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'baroness');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludge metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'baroness' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'baroness' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'baroness' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-metal', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'baroness' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'colourful', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'baroness' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Converge', 'converge', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'converge');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'mathcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'converge' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'converge' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'chaotic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'converge' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'converge' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'technical', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'converge' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'raw', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'converge' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Killswitch Engage', 'killswitch engage', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'killswitch engage');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'killswitch engage' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic death metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'killswitch engage' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'killswitch engage' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'anthemic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'killswitch engage' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Code Orange', 'code orange', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'code orange');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'code orange' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'industrial metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'code orange' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'code orange' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'experimental', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'code orange' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Turnstile', 'turnstile', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'turnstile');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'turnstile' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'alternative rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'turnstile' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'turnstile' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'energetic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'turnstile' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'crossover', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'turnstile' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Knocked Loose', 'knocked loose', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'knocked loose');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hardcore punk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'knocked loose' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'metalcore', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'knocked loose' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'aggressive', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'knocked loose' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'beatdown', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'knocked loose' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Russian Circles', 'russian circles', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'russian circles');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'post-metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'russian circles' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'instrumental rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'russian circles' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'russian circles' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'cinematic', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'russian circles' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'progressive', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'russian circles' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Chelsea Wolfe', 'chelsea wolfe', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'chelsea wolfe');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'doom folk', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'chelsea wolfe' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'gothic rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'chelsea wolfe' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'atmospheric', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'chelsea wolfe' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'dark', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'chelsea wolfe' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'ethereal', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'chelsea wolfe' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'experimental', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'chelsea wolfe' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Pallbearer', 'pallbearer', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'pallbearer');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'doom metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'pallbearer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'traditional doom', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'pallbearer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'pallbearer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melancholic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'pallbearer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'slow', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'pallbearer' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'clean vocals', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'pallbearer' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Khemmis', 'khemmis', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'khemmis');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'doom metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'khemmis' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'khemmis' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'melodic', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'khemmis' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'clean vocals', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'khemmis' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'khemmis' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'epic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'khemmis' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Clutch', 'clutch', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'clutch');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'stoner rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'clutch' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hard rock', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'clutch' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'blues rock', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'clutch' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'groove', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'clutch' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'clutch' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'storytelling', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'clutch' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Black Label Society', 'black label society', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'black label society');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'heavy metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'black label society' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'southern metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'black label society' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'guitar solos', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'black label society' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'hard rock', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'black label society' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'riff-driven', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'black label society' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'classic', 0.4, 'lastfm' FROM dim_artist WHERE name_normalized = 'black label society' ON CONFLICT DO NOTHING;

INSERT INTO dim_artist (name, name_normalized, country)
SELECT 'Thou', 'thou', 'US'
WHERE NOT EXISTS (SELECT 1 FROM dim_artist WHERE name_normalized = 'thou');
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'sludge metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'thou' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'doom metal', 1.0, 'musicbrainz' FROM dim_artist WHERE name_normalized = 'thou' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'harsh vocals', 0.85, 'lastfm' FROM dim_artist WHERE name_normalized = 'thou' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'nihilistic', 0.7, 'lastfm' FROM dim_artist WHERE name_normalized = 'thou' ON CONFLICT DO NOTHING;
INSERT INTO artist_tag (artist_id, tag, weight, source) SELECT artist_id, 'slow', 0.55, 'lastfm' FROM dim_artist WHERE name_normalized = 'thou' ON CONFLICT DO NOTHING;

COMMIT;
