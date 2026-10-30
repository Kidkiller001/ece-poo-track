from datetime import date, datetime, timedelta

from json_connection import JsonConnection
from festival_repository import FestivalRepository
from performance_validator import validate_performance, festival_day
from solo import Solo
from lineup import Lineup
from workshop import Workshop


def performance_id(performance):
    start = datetime.fromisoformat(performance.start)
    return f"{performance.venue.slug}-{start:%Y-%m-%d-%H%M}"


def get_performance_kind(performance):
    return performance.kind


def get_performance_end(performance):
    return performance.end_datetime


class Festival:
    """Domain object coordinating festival data and business operations."""

    def __init__(self, json_connection, repository=None):
        self.json_connection = json_connection
        self.repository = repository or FestivalRepository(json_connection)

    @property
    def name(self):
        return self.json_connection.data["name"]

    @property
    def first_day(self):
        return date.fromisoformat(self.json_connection.data["first_day"])

    @property
    def last_day(self):
        return date.fromisoformat(self.json_connection.data["last_day"])

    @property
    def days(self):
        return [
            self.first_day + timedelta(days=offset)
            for offset in range((self.last_day - self.first_day).days + 1)
        ]

    @property
    def venues(self):
        return self.repository.venues

    @property
    def artists(self):
        return self.repository.artists

    @property
    def performances(self):
        return self.repository.performances

    def get_venue(self, slug):
        return self.repository.get_venue(slug)

    def get_artist(self, slug):
        return self.repository.get_artist(slug)

    def get_performance(self, performance_id_value):
        return self.repository.get_performance(performance_id_value)

    def performances_for_artist(self, slug):
        return sorted(self.repository.performances_for_artist(slug))

    def programme_for_day(self, day):
        if isinstance(day, str):
            day = date.fromisoformat(day)
        performances = [
            p for p in self.performances
            if festival_day(datetime.fromisoformat(p.start)) == day
        ]
        return sorted(
            performances,
            key=lambda p: (
                p.start_datetime.hour + (24 if p.start_datetime.hour < 6 else 0),
                p.start_datetime.minute,
                p.venue.name.casefold(),
            ),
        )

    def programme(self, day=None, venue=None):
        results = self.performances
        if day is not None:
            if isinstance(day, str):
                day = date.fromisoformat(day)
            results = [
                p for p in results
                if datetime.fromisoformat(p.start).date() == day
            ]
        if venue is not None:
            results = [p for p in results if p.venue.slug == venue]
        return sorted(results)

    def now_playing(self, moment=None):
        moment = moment or datetime.now()
        if isinstance(moment, str):
            moment = datetime.fromisoformat(moment)
        return sorted(
            p for p in self.performances
            if p.start_datetime <= moment < p.end_datetime
        )

    def up_next(self, moment=None, limit=3):
        moment = moment or datetime.now()
        if isinstance(moment, str):
            moment = datetime.fromisoformat(moment)
        return sorted(
            p for p in self.performances
            if p.start_datetime > moment
        )[:limit]

    def add_performance(self, performance):
        """Validate, persist and register a performance atomically."""
        validate_performance(
            performance=performance,
            venues=self.venues,
            artists=list(self.artists.values()),
            performances=self.performances,
            first_day=self.first_day.isoformat(),
            last_day=self.last_day.isoformat(),
        )

        record = performance.to_dict()
        records = self.json_connection.data["performances"]
        records.append(record)
        try:
            self.json_connection.save()
        except Exception:
            records.remove(record)
            raise

        self.performances.append(performance)
        return performance

    def cancel_performance(self, performance_id_value):
        performance = self.get_performance(performance_id_value)
        if performance is None:
            raise ValueError(
                f"Unknown performance ID '{performance_id_value}'."
            )

        records = self.json_connection.data["performances"]
        record = next(
            (
                item for item in records
                if (
                    item["venue"] + "-"
                    + datetime.fromisoformat(item["start"]).strftime(
                        "%Y-%m-%d-%H%M"
                    )
                ) == performance_id(performance)
            ),
            None,
        )
        if record is None:
            raise ValueError(
                f"Could not find performance data for "
                f"'{performance_id(performance)}'."
            )

        records.remove(record)
        try:
            self.json_connection.save()
        except Exception:
            records.append(record)
            raise

        self.performances.remove(performance)
        return performance


# Lazily create the shared application instance. This keeps importing
# Festival safe for tests that construct it with an isolated data source.
_default_festival = None


def get_default_festival():
    global _default_festival
    if _default_festival is None:
        _default_festival = Festival(JsonConnection())
    return _default_festival


def add_performance():
    festival = get_default_festival()
    title = input("Title: ").strip()
    artist_slug = input("Artist (slug): ").strip().lower()
    venue_slug = input("Venue (slug): ").strip().lower()
    start = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_input = input("Duration (minutes): ").strip()

    try:
        duration = int(duration_input)
    except ValueError:
        print(f"Error: '{duration_input}' is not a number of minutes.")
        return

    try:
        datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except ValueError:
        print("Error: Start must use the format YYYY-MM-DDTHH:MM.")
        return

    artist = festival.get_artist(artist_slug)
    venue = festival.get_venue(venue_slug)

    if artist is None:
        print(f"Error: Unknown artist '{artist_slug}'.")
        return
    if venue is None:
        print(f"Error: Unknown venue '{venue_slug}'.")
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
        festival.add_performance(performance)
        print(
            f"Added: {performance_id(performance)}, "
            f"first line of programme {start[:10]}"
        )
    except ValueError as error:
        print(f"Error: {error}")


def cancel_performance(performance_id_to_cancel):
    festival = get_default_festival()
    performance = festival.cancel_performance(performance_id_to_cancel)
    print(f"Cancelled: {performance_id(performance)}")


def list_artist_performances(slug):
    festival = get_default_festival()
    artist = festival.get_artist(slug)
    if artist is None:
        print(f"No artist '{slug}'.")
        return

    performances = festival.performances_for_artist(slug)
    if not performances:
        print(f"No performances for '{artist.name}'.")
        return

    print(artist.name)
    for performance in performances:
        if isinstance(performance, Solo):
            role = "solo"
        elif isinstance(performance, Lineup):
            role = "host" if performance.host == artist else "act"
        elif isinstance(performance, Workshop):
            role = "teacher"
        else:
            role = "performance"

        start = performance.start_datetime
        end = performance.end_datetime
        print(
            f"{start.strftime('%a %d %H:%M')}-{end:%H:%M} "
            f"| {performance.venue.name} "
            f"| {performance.title} ({role})"
        )


def list_venues():
    festival = get_default_festival()
    total_capacity = 0
    for venue in festival.venues:
        print(f"{venue.slug}: {venue.name}, {venue.capacity} seats")
        total_capacity += venue.capacity
    print(f"Total: {total_capacity} seats")


def list_programme(day):
    festival = get_default_festival()
    programme_date = datetime.strptime(day, "%Y-%m-%d").date()
    performances = festival.programme_for_day(programme_date)
    if not performances:
        print(f"No performances on '{day}'.")
        return

    print(f"Programme for {programme_date.strftime('%A %d %B')}:")
    for performance in performances:
        print(performance)


def list_now(moment):
    festival = get_default_festival()
    moment = datetime.fromisoformat(moment)
    on_stage = festival.now_playing(moment)
    upcoming = festival.up_next(moment)

    print(f"On stage at {moment:%Y-%m-%d %H:%M}:")
    if on_stage:
        for performance in on_stage:
            print(
                f"- {performance.title} at {performance.venue.name}, "
                f"until {performance.end_datetime:%H:%M}"
            )
    else:
        print("- Nothing is currently on stage.")

    print("Up next:")
    for performance in upcoming:
        print(f"- {performance}")
