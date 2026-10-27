
from datetime import datetime, timedelta
import unicodedata

from solo import Solo
from lineup import Lineup
from workshop import Workshop


MIN_GAP = timedelta(minutes=30)


def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return text.lower().replace(" ", "-")


def performance_artists(performance):
    """Return all artists involved in a performance."""
    if isinstance(performance, Solo):
        return {performance.artist}

    if isinstance(performance, Lineup):
        return {performance.host, *performance.acts}

    if isinstance(performance, Workshop):
        return {performance.teacher}

    return set()


def validate_performance(
    performance,
    venues,
    artists,
    performances,
    first_day,
    last_day,
):
    """Validate a performance and raise ValueError on failure."""

    # Validate the venue
    venue_by_slug = {
        slugify(venue.name): venue.name
        for venue in venues
    }

    venue_slug = slugify(performance.venue)

    if venue_slug not in venue_by_slug:
        raise ValueError(
            f"Unknown venue '{performance.venue}'."
        )

    # Validate the start date and time
    try:
        start = datetime.fromisoformat(performance.start)
    except (ValueError, TypeError):
        raise ValueError(
            "Start must use the format YYYY-MM-DDTHH:MM."
        ) from None

    festival_start = datetime.strptime(
        first_day, "%Y-%m-%d"
    ).date()
    festival_end = datetime.strptime(
        last_day, "%Y-%m-%d"
    ).date()

    if not festival_start <= start.date() <= festival_end:
        raise ValueError(
            f"{start:%Y-%m-%d} is not a day of the festival."
        )

    # Validate duration
    if (
        not isinstance(performance.duration_minutes, int)
        or isinstance(performance.duration_minutes, bool)
        or not 1 <= performance.duration_minutes <= 360
    ):
        raise ValueError(
            "Duration must be between 1 and 360 minutes."
        )

    # Validate every artist, including hosts, acts and teachers
    artist_by_slug = {
        slugify(artist["name"]): artist["name"]
        for artist in artists
    }

    involved_artists = {
        slugify(artist)
        for artist in performance_artists(performance)
    }

    for artist_slug in sorted(involved_artists):
        if artist_slug not in artist_by_slug:
            raise ValueError(
                f"Unknown artist '{artist_slug}'."
            )

    end = start + timedelta(
        minutes=performance.duration_minutes
    )

    # Check venue availability and artist availability
    for existing in performances:
        existing_start = datetime.fromisoformat(existing.start)
        existing_end = existing_start + timedelta(
            minutes=existing.duration_minutes
        )

        # A gap of exactly 30 minutes is allowed.
        conflict = (
            start < existing_end + MIN_GAP
            and existing_start < end + MIN_GAP
        )

        if not conflict:
            continue

        # Report venue conflicts with the existing show's details.
        if slugify(existing.venue) == venue_slug:
            venue_name = venue_by_slug[venue_slug]

            raise ValueError(
                f"{venue_name} is busy with {existing.title} "
                f"({existing_start:%Y-%m-%d %H:%M}-"
                f"{existing_end:%H:%M})."
            )

        # Report the first shared artist's existing show.
        existing_artists = {
            slugify(artist)
            for artist in performance_artists(existing)
        }

        shared_artists = involved_artists & existing_artists

        if shared_artists:
            artist_slug = sorted(shared_artists)[0]
            artist_name = artist_by_slug[artist_slug]

            raise ValueError(
                f"{artist_name} is on stage in {existing.title}."
            )

    return True
