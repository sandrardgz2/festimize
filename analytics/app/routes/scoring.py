"""
Scoring and momentum endpoints.

PLACEHOLDER ROUTES ONLY. The request/response shapes below are final (they
mirror artist_score and artist_momentum in db/schema.sql), but the actual
recommender (taste matching against artist_tag) and the momentum measure
are the developer's own data-science deliverable for this capstone and are
deliberately NOT implemented here. Do not add TF-IDF, cosine similarity, or
any momentum calculation to this file — wire it up in the real
implementation, not in the scaffold.

Targets Python 3.9 syntax.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["scoring"])


# ---------------------------------------------------------------- /score
class ScoreRequest(BaseModel):
    # Room to force a recompute even if artist_score.computed_at is recent.
    force_recompute: bool = False


class ArtistScore(BaseModel):
    user_id: int
    artist_id: int
    match_score: float  # 0..1, matches artist_score.match_score
    computed_at: datetime


class ScoreResponse(BaseModel):
    user_id: int
    scores: List[ArtistScore]


@router.post("/score/{user_id}", response_model=ScoreResponse)
def score_user(
    user_id: int,
    payload: ScoreRequest,
    db: Session = Depends(get_db),
) -> ScoreResponse:
    """
    Recompute taste-match scores for a user across candidate artists and
    upsert them into artist_score.

    Not implemented: this is the recommender the developer is building as
    her data-science deliverable (taste matching over artist_tag).
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Scoring is not implemented yet. This endpoint is a placeholder "
            "for the taste-match recommender, to be built against "
            "dim_artist / artist_tag / artist_score."
        ),
    )


# ------------------------------------------------------------- /momentum
class MomentumResponse(BaseModel):
    artist_id: int
    momentum_score: float
    appearances: int
    first_year: Optional[int] = None
    last_year: Optional[int] = None
    computed_at: datetime


@router.get("/artists/{artist_id}/momentum", response_model=MomentumResponse)
def get_artist_momentum(
    artist_id: int,
    db: Session = Depends(get_db),
) -> MomentumResponse:
    """
    Return the cached rising-artist measure for one artist from
    artist_momentum.

    Not implemented: the momentum measure itself (how billing_rank/
    size_rank trends across editions turn into a 0..1 score) is the
    developer's own deliverable.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Momentum is not implemented yet. This endpoint is a "
            "placeholder for the rising-artist measure, to be written into "
            "and read from artist_momentum."
        ),
    )
