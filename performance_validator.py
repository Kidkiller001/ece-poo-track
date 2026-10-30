from datetime import datetime, timedelta

from helper import slugify
from solo import Solo
from lineup import Lineup
from workshop import Workshop


MIN_GAP = timedelta(minutes=30)


def _artist_slug(artist):
    """Accept either an Artist object or a slug/name string."""
    if hasattr(artist, "slug"):
        return artist.slug
    return slugify(str(artist))


def performance_artists(performance):
    """Return every artist involved, represented by their slugs."""
    if isinstance(performance, Solo):
        artists = [performance.artist]
    elif isinstance(performance, Lineup):
        artists = [performance.host, *performance.acts]
    elif isinstance(performance, Workshop):
        artists = [performance.teacher]
    else:
        artists = []

    return {_artist_slug(artist) for artist in artists}


def performance_venue_slug(performance):
    venue = performance.venue
    return venue.slug if hasattr(venue, "slug") else slugify(str(venue))


def festival_day(start):
    """Assign performances before 06:00 to the previous programme day."""
    if start.hour < 6:
        return (start - timedelta(days=1)).date()
    return start.date()


def validate_performance(
    performance,
    venues,
    artists,
    performances,
    first_day,
    last_day,
):
    """Validate a performance and raise ValueError when a rule is broken."""

    venue_slugs = {
        venue.slug if hasattr(venue, "slug") else slugify(str(venue))
        for venue in venues
    }
    venue_slug = performance_venue_slug(performance)

    if venue_slug not in venue_slugs:
        raise ValueError(f"Unknown venue '{venue_slug}'.")

    try:
        start = datetime.fromisoformat(performance.start)
    except (ValueError, TypeError):
        raise ValueError(
            "Start must use the format YYYY-MM-DDTHH:MM."
        ) from None

    first = datetime.strptime(first_day, "%Y-%m-%d").date()
    last = datetime.strptime(last_day, "%Y-%m-%d").date()
    programme_day = festival_day(start)

    if not first <= programme_day <= last:
        raise ValueError(
            f"{programme_day:%Y-%m-%d} is not a day of the festival."
        )

    duration = performance.duration_minutes
    if (
        not isinstance(duration, int)
        or isinstance(duration, bool)
        or not 1 <= duration <= 360
    ):
        raise ValueError("Duration must be between 1 and 360 minutes.")

    known_artist_slugs = {
        artist.slug if hasattr(artist, "slug")
        else slugify(artist["name"])
        for artist in artists
    }
    involved = performance_artists(performance)

    for slug in sorted(involved):
        if slug not in known_artist_slugs:
            raise ValueError(f"Unknown artist '{slug}'.")

    end = start + timedelta(minutes=duration)

    for existing in performances:
        existing_start = datetime.fromisoformat(existing.start)
        existing_end = existing_start + timedelta(
            minutes=existing.duration_minutes
        )

        # A 30-minute gap is sufficient; overlaps or shorter gaps conflict.
        conflict = (
            start < existing_end + MIN_GAP
            and existing_start < end + MIN_GAP
        )
        if not conflict:
            continue

        if performance_venue_slug(existing) == venue_slug:
            venue_name = next(
                (
                    v.name for v in venues
                    if (v.slug if hasattr(v, "slug") else slugify(str(v)))
                    == venue_slug
                ),
                venue_slug,
            )
            raise ValueError(
                f"{venue_name} is busy with {existing.title} "
                f"({existing_start:%Y-%m-%d %H:%M}-"
                f"{existing_end:%H:%M})."
            )

        shared = involved & performance_artists(existing)
        if shared:
            slug = sorted(shared)[0]
            artist_name = next(
                (
                    a.name if hasattr(a, "name") else a["name"]
                    for a in artists
                    if (a.slug if hasattr(a, "slug")
                        else slugify(a["name"])) == slug
                ),
                slug,
            )
            raise ValueError(
                f"{artist_name} is on stage in {existing.title}."
            )

    return True
