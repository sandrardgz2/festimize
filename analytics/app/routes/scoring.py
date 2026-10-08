"""
Scoring and momentum endpoints.

/score/{user_id} is implemented: it builds a taste profile from the artists a
user saved, scores every artist against it (see app/recommender.py), and
caches the result in artist_score so page loads are a read.

/artists/{artist_id}/momentum is still a placeholder: the rising-artist
measure needs the historical lineup data, which arrives in the next phase.

Targets Python 3.9 syntax.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.recommender import build_matrix, score_against_profile

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
    Score every artist for one user and cache the result.

    Returns an empty list when the user has saved no artists: there is no
    profile to match against, and a made-up number would be worse than none.
    """
    tag_rows = db.execute(
        text("select artist_id, tag, weight from artist_tag")
    ).fetchall()
    if not tag_rows:
        raise HTTPException(status_code=409, detail="No artist tags loaded; seed the database first.")

    saved = [
        r[0] for r in db.execute(
            text("select artist_id from user_artist where user_id = :uid"),
            {"uid": user_id},
        ).fetchall()
    ]

    tfidf, artist_ids = build_matrix([(r[0], r[1], float(r[2])) for r in tag_rows])
    scores = score_against_profile(tfidf, artist_ids, saved)

    if scores:
        db.execute(
            text(
                """
                insert into artist_score (user_id, artist_id, match_score, computed_at)
                values (:uid, :aid, :score, now())
                on conflict (user_id, artist_id)
                do update set match_score = excluded.match_score,
                              computed_at = excluded.computed_at
                """
            ),
            [{"uid": user_id, "aid": aid, "score": round(s, 4)} for aid, s in scores.items()],
        )
        db.commit()

    now = datetime.now(timezone.utc)
    return ScoreResponse(
        user_id=user_id,
        scores=[
            ArtistScore(user_id=user_id, artist_id=aid, match_score=s, computed_at=now)
            for aid, s in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        ],
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
