from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from festival import get_default_festival


app = FastAPI(title="Deauville Festival du Rire 2027")


def get_domain():
    return get_default_festival()


def serialize_performance(performance):
    return performance.to_dict()


def serialize_venue(venue):
    return {
        "slug": venue.slug,
        "name": venue.name,
        "capacity": venue.capacity,
        "address": venue.address,
    }


def serialize_artist(artist):
    return artist.to_dict()


@app.get("/api/festival")
def get_festival():
    return {
        "name": get_domain().name,
        "first_day": get_domain().first_day.isoformat(),
        "last_day": get_domain().last_day.isoformat(),
        "days": [day.isoformat() for day in get_domain().days],
    }


@app.get("/api/venues")
def get_venues():
    return [serialize_venue(v) for v in get_domain().venues]


@app.get("/api/artists")
def get_artists():
    artists = sorted(get_domain().artists.values(), key=lambda a: a.slug)
    return [serialize_artist(a) for a in artists]


@app.get("/api/artists/{slug}")
def get_artist(slug: str):
    artist = get_domain().get_artist(slug)
    if artist is None:
        raise HTTPException(
            status_code=404,
            detail=f"No artist found with slug '{slug}'.",
        )
    result = serialize_artist(artist)
    result["performances"] = [
        serialize_performance(p)
        for p in get_domain().performances_for_artist(slug)
    ]
    return result


@app.get("/api/programme")
def get_programme(day: date | None = None, venue: str | None = None):
    return [
        serialize_performance(p)
        for p in get_domain().programme(day=day, venue=venue)
    ]


@app.get("/api/performances/{performance_id_value}")
def get_performance(performance_id_value: str):
    performance = get_domain().get_performance(performance_id_value)
    if performance is None:
        raise HTTPException(
            status_code=404,
            detail=f"No performance found with id '{performance_id_value}'.",
        )
    return serialize_performance(performance)


@app.get("/api/now")
def get_now(at: str | None = None):
    try:
        moment = datetime.fromisoformat(at) if at else datetime.now()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="'at' must be a valid ISO datetime.",
        ) from None

    return {
        "now_playing": [
            serialize_performance(p) for p in get_domain().now_playing(moment)
        ],
        "up_next": [
            serialize_performance(p) for p in get_domain().up_next(moment, limit=3)
        ],
    }


public_dir = Path(__file__).resolve().parent / "web" / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="web")
