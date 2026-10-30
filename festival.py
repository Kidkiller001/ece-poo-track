
from datetime import datetime, timedelta

from json_connection import JsonConnection
from festival_repository import FestivalRepository
from performance_validator import validate_performance

from solo import Solo
from lineup import Lineup
from workshop import Workshop

from helper import slugify


# ---------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------

json_connection = JsonConnection()
festival_repository = FestivalRepository(json_connection)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def performance_id(performance):
    """Build a performance ID from its venue and start time."""

    start = datetime.fromisoformat(performance.start)

    return (
        f"{performance.venue.slug}-"
        f"{start:%Y-%m-%d-%H%M}"
    )


def get_performance_kind(performance):
    """Return the type of a performance."""

    if isinstance(performance, Solo):
        return "solo"

    if isinstance(performance, Lineup):
        return "lineup"

    if isinstance(performance, Workshop):
        return "workshop"

    return "performance"


def get_performance_end(performance):
    """Calculate the end time of a performance."""

    start = datetime.fromisoformat(performance.start)

    return start + timedelta(minutes=performance.duration_minutes)


# ---------------------------------------------------------
# ADD PERFORMANCE
# ---------------------------------------------------------

def add_performance():
    title = input("Title: ").strip()
    artist_slug = input("Artist (slug): ").strip().lower()
    venue_slug = input("Venue (slug): ").strip().lower()
    start = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_input = input("Duration (minutes): ").strip()

    # Validate duration.
    try:
        duration = int(duration_input)
    except ValueError:
        print(
            f"Error: '{duration_input}' is not a number of minutes."
        )
        return

    # Validate date format.
    try:
        datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except ValueError:
        print(
            "Error: Start must use the format YYYY-MM-DDTHH:MM."
        )
        return

    # Resolve the relationships.
    artist = festival_repository.get_artist(artist_slug)
    venue = festival_repository.get_venue(venue_slug)

    if artist is None:
        print(f"Error: Unknown artist '{artist_slug}'.")
        return

    if venue is None:
        print(f"Error: Unknown venue '{venue_slug}'.")
        return

    # Create a temporary performance using the original
    # string-based values expected by the existing validator.
    candidate = Solo(
        title=title,
        venue=venue_slug,
        start=start,
        duration_minutes=duration,
        description="",
        artist=artist_slug,
        min_age=0
    )

    try:
        validate_performance(
            performance=candidate,
            venues=festival_repository.venues,
            artists=json_connection.data["artists"],
            performances=festival_repository.performances,
            first_day=json_connection.data["first_day"],
            last_day=json_connection.data["last_day"],
        )

        # Create the actual object with object relationships.
        performance = Solo(
            title=title,
            venue=venue,
            start=start,
            duration_minutes=duration,
            description="",
            artist=artist,
            min_age=0
        )

        # Persist the original JSON representation.
        record = {
            "kind": "solo",
            "title": title,
            "venue": venue_slug,
            "start": start,
            "duration_minutes": duration,
            "description": "",
            "artist": artist_slug,
            "min_age": 0,
        }

        json_connection.data["performances"].append(record)
        json_connection.save()

        # Update the in-memory repository.
        festival_repository.performances.append(performance)

        print(
            f"Added: {performance_id(performance)}, "
            f"first line of programme {start[:10]}"
        )

    except ValueError as error:
        print(f"Error: {error}")


# ---------------------------------------------------------
# CANCEL PERFORMANCE
# ---------------------------------------------------------

def cancel_performance(performance_id_to_cancel):
    """Cancel a performance and persist the change."""

    performance = next(
        (
            item
            for item in festival_repository.performances
            if performance_id(item) == performance_id_to_cancel
        ),
        None
    )

    if performance is None:
        raise ValueError(
            f"Unknown performance ID '{performance_id_to_cancel}'."
        )

    target_id = performance_id(performance)

    # Find the corresponding JSON record.
    records = json_connection.data["performances"]

    record_to_remove = next(
        (
            record
            for record in records
            if (
                record["venue"]
                + "-"
                + datetime.fromisoformat(record["start"]).strftime(
                    "%Y-%m-%d-%H%M"
                )
            ) == target_id
        ),
        None
    )

    if record_to_remove is None:
        raise ValueError(
            f"Could not find performance data for '{target_id}'."
        )

    records.remove(record_to_remove)

    # Persist the updated JSON.
    json_connection.save()

    # Update the in-memory repository.
    festival_repository.performances.remove(performance)

    print(f"Cancelled: {target_id}")


# ---------------------------------------------------------
# LIST ARTIST PERFORMANCES
# ---------------------------------------------------------

def list_artist_performances(slug):
    """Display all performances involving an artist."""

    artist = festival_repository.get_artist(slug)

    if artist is None:
        print(f"No artist '{slug}'.")
        return

    artist_performances = (
        festival_repository.performances_for_artist(slug)
    )

    if not artist_performances:
        print(f"No performances for '{artist.name}'.")
        return

    print(artist.name)

    # Determine the artist's role in each performance.
    performances_with_roles = []

    for performance in artist_performances:

        if isinstance(performance, Solo):
            role = "solo"

        elif isinstance(performance, Lineup):
            if performance.host == artist:
                role = "host"
            else:
                role = "act"

        elif isinstance(performance, Workshop):
            role = "teacher"

        else:
            role = "performance"

        performances_with_roles.append((performance, role))

    # Sort chronologically.
    performances_with_roles.sort(
        key=lambda item: datetime.fromisoformat(item[0].start)
    )

    for performance, role in performances_with_roles:
        start = datetime.fromisoformat(performance.start)
        end = get_performance_end(performance)

        print(
            f"{start.strftime('%a %d %H:%M')}-{end:%H:%M} "
            f"| {performance.venue.name} "
            f"| {performance.title} ({role})"
        )


# ---------------------------------------------------------
# LIST VENUES
# ---------------------------------------------------------

def list_venues():
    """Display all festival venues and their total capacity."""

    total_capacity = 0

    for venue in festival_repository.venues:
        print(
            f"{venue.slug}: {venue.name}, "
            f"{venue.capacity} seats"
        )

        total_capacity += venue.capacity

    print(f"Total: {total_capacity} seats")


# ---------------------------------------------------------
# LIST PROGRAMME
# ---------------------------------------------------------

def list_programme(day):
    """Display all performances belonging to a festival day."""

    programme_date = datetime.strptime(
        day, "%Y-%m-%d"
    ).date()

    def festival_day(performance):
        start = datetime.fromisoformat(performance.start)

        # Performances before 06:00 belong to the previous
        # evening's programme.
        if start.hour < 6:
            return (start - timedelta(days=1)).date()

        return start.date()

    daily_performances = [
        performance
        for performance in festival_repository.performances
        if festival_day(performance) == programme_date
    ]

    if not daily_performances:
        print(f"No performances on '{day}'.")
        return

    print(
        f"Programme for {programme_date.strftime('%A %d %B')}:"
    )

    # Sort after-midnight performances as part of the previous
    # evening's programme.
    daily_performances.sort(
        key=lambda performance: (
            datetime.fromisoformat(performance.start).hour
            + (
                24
                if datetime.fromisoformat(performance.start).hour < 6
                else 0
            ),
            datetime.fromisoformat(performance.start).minute
        )
    )

    for performance in daily_performances:
        start = datetime.fromisoformat(performance.start)
        end = get_performance_end(performance)

        kind = get_performance_kind(performance)

        print(
            f"{start:%H:%M}-{end:%H:%M} | "
            f"{performance.venue.name} | "
            f"{performance.title} ({kind})"
        )


# ---------------------------------------------------------
# CURRENTLY ON STAGE
# ---------------------------------------------------------

def list_now(moment):
    """Display performances currently happening and what comes next."""

    moment = datetime.fromisoformat(moment)

    schedule = []

    for performance in festival_repository.performances:
        start = datetime.fromisoformat(performance.start)
        end = get_performance_end(performance)

        schedule.append({
            "performance": performance,
            "start": start,
            "end": end,
            "venue": performance.venue.name,
        })

    schedule.sort(key=lambda item: item["start"])

    # Find performances currently happening.
    on_stage = [
        item
        for item in schedule
        if item["start"] <= moment < item["end"]
    ]

    print(f"On stage at {moment:%Y-%m-%d %H:%M}:")

    if on_stage:
        for item in on_stage:
            performance = item["performance"]

            print(
                f"- {performance.title} at {item['venue']}, "
                f"until {item['end']:%H:%M}"
            )

    else:
        print("- Nothing is currently on stage.")

    # Find the next three performances.
    upcoming = [
        item
        for item in schedule
        if item["start"] > moment
    ][:3]

    print("Up next:")

    for item in upcoming:
        performance = item["performance"]
        kind = get_performance_kind(performance)

        print(
            f"- {item['start']:%H:%M}-{item['end']:%H:%M} "
            f"| {item['venue']} | "
            f"{performance.title} ({kind})"
        )
