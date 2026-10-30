
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from json_connection import JsonConnection
from festival_repository import FestivalRepository

from solo import Solo
from lineup import Lineup
from workshop import Workshop


# ---------------------------------------------------------
# APPLICATION INITIALIZATION
# ---------------------------------------------------------

app = FastAPI(
    title="Deauville Festival du Rire 2027"
)

json_connection = JsonConnection()
festival_repository = FestivalRepository(json_connection)


# ---------------------------------------------------------
# SERIALIZATION HELPERS
# ---------------------------------------------------------

def serialize_performance(performance):
    """
    Convert a performance object into JSON-compatible data.

    Relationships are represented by slugs rather than
    returning entire Artist and Venue objects.
    """

    result = performance.to_dict()

    # Common attributes
    result["venue"] = performance.venue.slug

    # Type-specific attributes
    if isinstance(performance, Solo):
        result["kind"] = "solo"
        result["artist"] = performance.artist.slug

    elif isinstance(performance, Lineup):
        result["kind"] = "lineup"
        result["host"] = performance.host.slug
        result["acts"] = [
            artist.slug for artist in performance.acts
        ]

    elif isinstance(performance, Workshop):
        result["kind"] = "workshop"
        result["teacher"] = performance.teacher.slug

    return result


def serialize_venue(venue):
    """Convert a Venue object into JSON-compatible data."""

    return {
        "slug": venue.slug,
        "name": venue.name,
        "capacity": venue.capacity,
        "address": venue.address,
    }


def serialize_artist(artist):
    """Convert an Artist object into JSON-compatible data."""

    return artist.to_dict()


# ---------------------------------------------------------
# FESTIVAL
# ---------------------------------------------------------

@app.get("/api/festival")
def get_festival():
    data = json_connection.data

    first_day = date.fromisoformat(data["first_day"])
    last_day = date.fromisoformat(data["last_day"])

    days = [
        (first_day + timedelta(days=i)).isoformat()
        for i in range((last_day - first_day).days + 1)
    ]

    return {
        "name": data["name"],
        "first_day": first_day.isoformat(),
        "last_day": last_day.isoformat(),
        "days": days,
    }


# ---------------------------------------------------------
# VENUES
# ---------------------------------------------------------

@app.get("/api/venues")
def get_venues():
    return [
        serialize_venue(venue)
        for venue in festival_repository.venues
    ]


# ---------------------------------------------------------
# ARTISTS
# ---------------------------------------------------------

@app.get("/api/artists")
def get_artists():
    artists = sorted(
        festival_repository.artists.values(),
        key=lambda artist: artist.slug
    )

    return [
        serialize_artist(artist)
        for artist in artists
    ]


@app.get("/api/artists/{slug}")
def get_artist(slug: str):
    artist = festival_repository.get_artist(slug)

    if artist is None:
        raise HTTPException(
            status_code=404,
            detail=f"No artist found with slug '{slug}'."
        )

    result = serialize_artist(artist)

    result["performances"] = [
        serialize_performance(performance)
        for performance in (
            festival_repository.performances_for_artist(slug)
        )
    ]

    return result


# ---------------------------------------------------------
# PROGRAMME
# ---------------------------------------------------------

@app.get("/api/programme")
def get_programme(
    day: date | None = None,
    venue: str | None = None,
):
    performances = festival_repository.list_performances(
        day=day,
        venue=venue,
    )

    return [
        serialize_performance(performance)
        for performance in performances
    ]


# ---------------------------------------------------------
# INDIVIDUAL PERFORMANCES
# ---------------------------------------------------------

@app.get("/api/performances/{performance_id}")
def get_performance(performance_id: str):
    performance = festival_repository.get_performance(
        performance_id
    )

    if performance is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No performance found with id '{performance_id}'."
            )
        )

    return serialize_performance(performance)


# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------

public_dir = Path(__file__).resolve().parent / "web" / "public"

app.mount(
    "/",
    StaticFiles(directory=public_dir, html=True),
    name="web"
)
