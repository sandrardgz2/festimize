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
  3. The taste profile is the average of the rows for the artists you saved.
  4. Score every artist by cosine similarity to that profile. Rows are unit
     length after step 2, so cosine is just a dot product.

Targets Python 3.9 syntax.
"""
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy import sparse
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


def score_against_profile(tfidf, artist_ids: List[int], saved_artist_ids: Sequence[int]) -> Dict[int, float]:
    """
    Score every artist against the taste profile built from saved_artist_ids.

    Returns artist_id -> score in 0..1. An empty profile scores nothing:
    better to show no numbers than to invent them.
    """
    index_of = {a: i for i, a in enumerate(artist_ids)}
    saved_rows = [index_of[a] for a in saved_artist_ids if a in index_of]
    if not saved_rows:
        return {}

    # The profile is the centroid of the saved artists, re-normalised so the
    # similarity below stays within 0..1.
    profile = np.asarray(tfidf[saved_rows].mean(axis=0)).ravel()
    norm = np.linalg.norm(profile)
    if norm == 0:
        return {}
    profile = profile / norm

    similarities = tfidf.dot(profile)  # rows are unit length, so this is cosine
    return {artist_ids[i]: float(max(0.0, min(1.0, s))) for i, s in enumerate(similarities)}
