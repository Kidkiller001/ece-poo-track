import json
import sys
from venue import Venue
from performance import Performance
from lineup import Lineup
from workshop import Workshop
from solo import Solo
from collections import Counter
import unicodedata
from json_connection import JsonConnection
from datetime import datetime, timedelta
from festival_repository import FestivalRepository
from performance_validator import validate_performance

json_connection = JsonConnection()
festival_repository = FestivalRepository(json_connection)
def performance_id(performance):
    start = datetime.fromisoformat(performance.start)
    return f"{performance.venue}-{start:%Y-%m-%d-%H%M}"
def add_performance():
    title = input("Title: ").strip()
    artist = input("Artist (slug): ").strip().lower()
    venue = input("Venue (slug): ").strip().lower()
    start = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_input = input("Duration (minutes): ").strip()

    # Parse duration with a user-friendly error message.
    try:
        duration = int(duration_input)
    except ValueError:
        print(
            f"Error: '{duration_input}' is not a number of minutes."
        )
        return

    # Validate the date format.
    try:
        datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except ValueError:
        print(
            "Error: Start must use the format YYYY-MM-DDTHH:MM."
        )
        return

    performance = Solo(
        title=title,
        venue=venue,
        start=start,
        duration_minutes=duration,
        description="",
        artist=artist,
        min_age=0,
    )

    try:
        validate_performance(
            performance=performance,
            venues=festival_repository.venues,
            artists=json_connection.data["artists"],
            performances=festival_repository.performances,
            first_day=json_connection.data["first_day"],
            last_day=json_connection.data["last_day"],
        )

        # Prepare the JSON record.
        record = {
            "kind": "solo",
            "title": title,
            "venue": venue,
            "start": start,
            "duration_minutes": duration,
            "description": "",
            "artist": artist,
            "min_age": 0,
        }

        # Save through JsonConnection.
        json_connection.data["performances"].append(record)
        json_connection.save()

        # Keep the in-memory repository in sync.
        festival_repository.performances.append(performance)

        performance_id = (
            f"{venue}-{start[:10]}-{start[11:16].replace(':', '')}"
        )

        print(
            f"Added: {performance_id}, "
            f"first line of programme {start[:10]}"
        )

    except ValueError as error:
        print(f"Error: {error}")

def performance_id(performance):
    """Build an ID from the venue slug and performance start."""
    start = datetime.fromisoformat(performance.start)

    return (
        f"{slugify(performance.venue)}-"
        f"{start:%Y-%m-%d-%H%M}"
    )


def cancel_performance(performance_id_to_cancel):
    """Cancel a performance by its ID and save the festival data."""

    matches = [
        performance
        for performance in festival_repository.performances
        if performance_id(performance) == performance_id_to_cancel
    ]

    if not matches:
        raise ValueError(
            f"Unknown performance ID '{performance_id_to_cancel}'."
        )

    performance = matches[0]
    target_id = performance_id(performance)

    # Find the corresponding raw JSON record.
    records = json_connection.data["performances"]

    record_to_remove = next(
        (
            record for record in records
            if (
                slugify(record["venue"])
                + "-"
                + datetime.fromisoformat(record["start"]).strftime(
                    "%Y-%m-%d-%H%M"
                )
            ) == target_id
        ),
        None,
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

def list_artist_performances(slug):
    artist_performances = []
    venues = festival_repository.venues
    performances = festival_repository.performances

    for performance in performances:
        if isinstance(performance, Solo):
            artist_name = performance.artist
            role = "solo"

        elif isinstance(performance, Lineup):
            artist_name = performance.host
            role = "host"

        else:
            continue

        if slugify(artist_name) == slug:
            artist_performances.append((performance, role))

    # Also find artists appearing as acts in a lineup
    for performance in performances:
        if isinstance(performance, Lineup):
            for act in performance.acts:
                if slugify(act) == slug:
                    artist_performances.append((performance, "act"))

    if not artist_performances:
        print(f"No artist '{slug}'.")
        return

    # Use the artist's display name
    first_performance, _ = artist_performances[0]
    if slugify(getattr(first_performance, "artist", "")) == slug:
        print(first_performance.artist)
    elif slugify(getattr(first_performance, "host", "")) == slug:
        print(first_performance.host)
    else:
        print(slug.replace("-", " ").title())

    venue_by_slug = {slugify(v.name): v.name for v in venues}

    for performance, role in sorted(
        artist_performances,
        key=lambda item: datetime.fromisoformat(item[0].start)
    ):
        start = datetime.fromisoformat(performance.start)
        end = start + timedelta(minutes=performance.duration_minutes)

        venue_name = venue_by_slug.get(
            slugify(performance.venue), performance.venue
        )

        print(
            f"{start.strftime('%a %d %H:%M')}-{end.strftime('%H:%M')} "
            f"| {venue_name} | {performance.title} ({role})"
        )
def list_venues():
    venues = festival_repository.venues
    total_capacity = 0

    for venue in venues:
        print(
            f"{slugify(venue.name)}: {venue.name}, "
            f"{venue.capacity} seats"
        )
        total_capacity += venue.capacity

    print(f"Total: {total_capacity} seats")
def list_programme(day):
    venues = festival_repository.venues
    performances = festival_repository.performances
    
    venue_names = {
        slugify(venue.name): venue.name
        for venue in venues
    }

    programme_date = datetime.strptime(day, "%Y-%m-%d").date()

    # Festival-day rule: performances starting before 06:00
    # belong to the previous evening's programme.
    def festival_day(perf):
        start = datetime.fromisoformat(perf.start)

        if start.hour < 6:
            return (start - timedelta(days=1)).date()

        return start.date()

    daily_performances = [
        perf for perf in performances
        if festival_day(perf) == programme_date
    ]

    if not daily_performances:
        print(f"No performances on '{day}'.")
        return

    print(f"Programme for {programme_date.strftime('%A %d %B')}:")

    # Treat after-midnight performances as continuing the previous evening.
    daily_performances.sort(
        key=lambda perf: (
            datetime.fromisoformat(perf.start).hour
            + (24 if datetime.fromisoformat(perf.start).hour < 6 else 0),
            datetime.fromisoformat(perf.start).minute
        )
    )

    for perf in daily_performances:
        start = datetime.fromisoformat(perf.start)
        end = start + timedelta(minutes=perf.duration_minutes)

        venue_name = venue_names.get(perf.venue, perf.venue)

        if isinstance(perf, Workshop):
            kind = "workshop"
        elif isinstance(perf, Lineup):
            kind = "lineup"
        elif isinstance(perf, Solo):
            kind = "solo"
        else:
            kind = "performance"

        print(
            f"{start:%H:%M}-{end:%H:%M} | "
            f"{venue_name} | {perf.title} ({kind})"
        )
def list_now(moment):
    venues = festival_repository.venues
    performances = festival_repository.performances
    moment = datetime.fromisoformat(moment)

    venue_by_slug = {
        slugify(venue.name): venue.name
        for venue in venues
    }

    # Calculate the start and end of every performance
    schedule = []

    for performance in performances:
        start = datetime.fromisoformat(performance.start)
        end = start + timedelta(
            minutes=performance.duration_minutes
        )

        venue_name = venue_by_slug.get(
            slugify(performance.venue),
            performance.venue
        )

        schedule.append({
            "performance": performance,
            "start": start,
            "end": end,
            "venue": venue_name,
        })

    schedule.sort(key=lambda item: item["start"])
    # print("\nDEBUG — Full schedule:")
    # for item in schedule:
        # print(
        #     item["start"],
        #     item["performance"].title,
        #     type(item["performance"]).__name__
        # )

    # Find performances currently on stage
    on_stage = [
        item for item in schedule
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

    # Find the next three performances
    upcoming = [
    item for item in schedule
    if item["start"] > moment
    ][:3]

    print("Up next:")

    for item in upcoming:
        performance = item["performance"]

        if isinstance(performance, Solo):
            kind = "solo"
        elif isinstance(performance, Lineup):
            kind = "lineup"
        elif isinstance(performance, Workshop):
            kind = "workshop"
        else:
            kind = "performance"

        print(
            f"- {item['start']:%H:%M}-{item['end']:%H:%M} "
            f"| {item['venue']} | {performance.title} ({kind})"
        )
def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return text.lower().replace(" ", "-")
def main():
    
    command = sys.argv[1] if len(sys.argv) > 1 else None

    if command == "venues":
        list_venues()
    elif command == "artist" and len(sys.argv) >= 3:
        artist_slug = sys.argv[2].lower()
        list_artist_performances(
            artist_slug,
        )
    elif command == "programme" and len(sys.argv) >= 3:
        day = sys.argv[2]
        list_programme(day)
    elif command == "now" and len(sys.argv) >= 3:
        list_now(
            sys.argv[2]
        )
    elif command == "add" and len(sys.argv) >= 2:
        add_performance()
    elif command == "cancel" and len(sys.argv) >= 3:
        performance_id_to_cancel = sys.argv[2]
        cancel_performance(performance_id_to_cancel)

if __name__ == "__main__":
    main()
