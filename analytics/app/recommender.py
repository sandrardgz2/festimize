"""
Taste matching.

The idea in one line: an artist scores highly when their descriptive tags
overlap with the tags of the artists you already love, and rare tags count
for more than common ones.

Why rare tags count more: on a metal lineup, "metal" tells you almost
nothing because nearly everyone carries it. "occult rock" tells you a great
deal, because only a handful of artists do. That weighting is what TF-IDF
does, so this uses scikit-learn's TfidfTransformer rather than hand-rolling it.

Pipeline:
  1. Build a sparse artist x tag matrix, where each cell holds the tag's
     weight (Last.fm counts carry real signal; MusicBrainz genres are 1.0).
  2. Apply TF-IDF so rare tags dominate and the rows are unit length.
  3. Build one to three cluster centroids from the saved artists, and take
     each saved artist as a profile in its own right. A single average fails
     anyone with range: four doom picks and four thrash picks average into a
     point that is neither. Clustering fixes most of that and not all of it —
     a corner of a taste held by only two artists never gets its own cluster —
     so the individual artists are kept alongside the centroids.
  4. Score every artist against each profile and keep its best score. An
     artist has to match one side of someone's taste well, not all of it.

Targets Python 3.9 syntax.
"""
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfTransformer


def build_matrix(rows: Sequence[Tuple[int, str, float]]):
    """
    Turn (artist_id, tag, weight) rows into a TF-IDF weighted sparse matrix.

    Returns the matrix plus the artist_id order, so a matrix row can be
    mapped back to an artist.
    """
    artist_ids = sorted({r[0] for r in rows})
    tags = sorted({r[1] for r in rows})
    artist_index = {a: i for i, a in enumerate(artist_ids)}
    tag_index = {t: i for i, t in enumerate(tags)}

    data, row_idx, col_idx = [], [], []
    for artist_id, tag, weight in rows:
        row_idx.append(artist_index[artist_id])
        col_idx.append(tag_index[tag])
        data.append(float(weight))

    counts = sparse.csr_matrix(
        (data, (row_idx, col_idx)), shape=(len(artist_ids), len(tags)), dtype=np.float64
    )
    # use_idf gives rare tags their weight; l2 makes every artist comparable
    # regardless of how many tags they happen to carry.
    tfidf = TfidfTransformer(use_idf=True, norm="l2").fit_transform(counts)
    return tfidf, artist_ids


def profile_count(saved: int) -> int:
    """
    How many cluster centroids to build for someone with this many saved artists.

    The cap was meant to stop one odd pick scoring a whole genre highly. It
    does not: k-means gives an outlier a cluster of its own, and the maximum
    over clusters then picks it up exactly as a single-artist profile would.
    Measured on the demo profile, adding one unrepresentative saved artist
    moved the nearest unsaved artist by +5.4 points under clustering and +5.4
    under the per-artist profiles it was supposed to protect against. The cap
    stays because fewer, broader centroids are still the right shape for the
    themes in a taste; it is simply not a defence.
    """
    if saved <= 3:
        return 1
    if saved <= 8:
        return 2
    return 3


def _profiles(tfidf, saved_rows: List[int], clustered: bool):
    """
    Unit-length taste profiles: a centroid per cluster, plus each saved artist.

    Two ideas of what a profile is, kept together because they fail in
    opposite directions. A centroid captures a theme that no single saved
    artist represents — it is what keeps Sevendust at 68% rather than 59%. A
    single artist captures a corner of a taste too small to form a cluster:
    three clusters built from a dozen artists cannot isolate a hardcore side
    represented by two of them, which is why Jesus Piece scored 22% against
    the centroids and 43% against Knocked Loose alone.

    Each artist keeps its best score across all of them, so adding the
    per-artist profiles can only raise a score, never lower one. Nothing the
    clustered version already matched gets worse.
    """
    dense = tfidf[saved_rows].toarray()
    k = profile_count(len(saved_rows)) if clustered else 1
    k = min(k, len(saved_rows))

    if k == 1:
        centroids = [dense.mean(axis=0)]
    else:
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(dense)
        centroids = [dense[labels == c].mean(axis=0) for c in range(k) if (labels == c).any()]

    if clustered:
        centroids = list(centroids) + [dense[i] for i in range(len(saved_rows))]

    out = []
    for v in centroids:
        norm = np.linalg.norm(v)
        if norm > 0:
            out.append(v / norm)
    return out


def score_against_profile(tfidf, artist_ids: List[int], saved_artist_ids: Sequence[int],
                          clustered: bool = True) -> Dict[int, float]:
    """
    Score every artist against the taste profile built from saved_artist_ids.

    Returns artist_id -> score in 0..1. An empty profile scores nothing:
    better to show no numbers than to invent them.

    clustered=False falls back to one averaged profile, which is what the
    first version did; kept so the two can be compared.
    """
    index_of = {a: i for i, a in enumerate(artist_ids)}
    saved_rows = [index_of[a] for a in saved_artist_ids if a in index_of]
    if not saved_rows:
        return {}

    profiles = _profiles(tfidf, saved_rows, clustered)
    if not profiles:
        return {}

    # Rows are unit length, so a dot product is cosine similarity. An artist
    # keeps its best score across the profiles: matching one side of someone's
    # taste well beats matching all of it weakly.
    best = None
    for profile in profiles:
        sims = tfidf.dot(profile)
        best = sims if best is None else np.maximum(best, sims)

    return {artist_ids[i]: float(max(0.0, min(1.0, s))) for i, s in enumerate(best)}
