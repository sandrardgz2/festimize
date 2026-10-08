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
  3. Cluster the saved artists into one to three taste profiles. A single
     average fails anyone with range: four doom picks and four thrash picks
     average into a point that is neither, so the artists that should score
     highest score middling instead. Clustering keeps the sides separate.
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
    How many taste profiles to build for someone with this many saved artists.

    Capped deliberately: with enough clusters every pick becomes its own
    profile, and then one odd choice scores a whole genre highly.
    """
    if saved <= 3:
        return 1
    if saved <= 8:
        return 2
    return 3


def _profiles(tfidf, saved_rows: List[int], clustered: bool):
    """Unit-length taste profiles: one centroid per cluster of saved artists."""
    dense = tfidf[saved_rows].toarray()
    k = profile_count(len(saved_rows)) if clustered else 1
    k = min(k, len(saved_rows))

    if k == 1:
        centroids = [dense.mean(axis=0)]
    else:
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(dense)
        centroids = [dense[labels == c].mean(axis=0) for c in range(k) if (labels == c).any()]

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
