"""
Tags on demand, for artists somebody has just chosen.

POST /tags/{artist_id} fetches an artist's tags from MusicBrainz and stores
them, so that an artist found through search can be scored like any other.
Returns how many were written; zero is a normal answer, not a failure — the
artist may have no MusicBrainz id, or none of their tags may survive the
vocabulary filter, or MusicBrainz may be slow. In every one of those cases
the artist stays saved and simply scores nothing until tags arrive.

Targets Python 3.9 syntax.
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.tags import fetch

log = logging.getLogger(__name__)
router = APIRouter()


class TagResponse(BaseModel):
    artist_id: int
    written: int
    already_had: int
    reason: str


@router.post("/tags/{artist_id}", response_model=TagResponse)
def tag_artist(artist_id: int, db: Session = Depends(get_db)) -> TagResponse:
    held = db.execute(
        text("select count(*) from artist_tag where artist_id = :a"),
        {"a": artist_id},
    ).scalar_one()
    if held:
        return TagResponse(artist_id=artist_id, written=0, already_had=held,
                           reason="already tagged")

    row = db.execute(
        text("select mbid, name from dim_artist where artist_id = :a"),
        {"a": artist_id},
    ).first()
    if row is None:
        return TagResponse(artist_id=artist_id, written=0, already_had=0,
                           reason="no such artist")
    if row.mbid is None:
        # 585 of the corpus artists never resolved to a MusicBrainz id. There
        # is nothing to look up, and guessing by name is how two artists who
        # share one get merged.
        return TagResponse(artist_id=artist_id, written=0, already_had=0,
                           reason="no MusicBrainz id to look up")

    found = fetch(str(row.mbid))
    if not found:
        return TagResponse(artist_id=artist_id, written=0, already_had=0,
                           reason="MusicBrainz has no usable tags for them")

    for tag, weight in found.items():
        db.execute(
            text("""insert into artist_tag (artist_id, tag, weight, source)
                    values (:a, :t, :w, 'musicbrainz')
                    on conflict do nothing"""),
            {"a": artist_id, "t": tag, "w": float(max(1, weight))},
        )
    db.commit()
    log.info("tagged %s with %d tags", row.name, len(found))
    return TagResponse(artist_id=artist_id, written=len(found), already_had=0,
                       reason="fetched from MusicBrainz")
