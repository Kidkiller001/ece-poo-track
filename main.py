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

json_connection = JsonConnection()

def list_artist_performances(artist_slug):
    venues = [
        Venue(v["name"], v["capacity"], v["address"])
        for v in json_connection.venues
    ]
    
    performances = []

    for performance in json_connection.performances:
        kind = performance["kind"]

        if kind == "solo":
            p = Solo(
                title=performance["title"],
                venue=performance["venue"],
                start=performance["start"],
                duration_minutes=performance["duration_minutes"],
                description=performance["description"],
                artist=performance["artist"],
                min_age=performance["min_age"]
            )

        elif kind == "lineup":
            p = Lineup(
                title=performance["title"],
                venue=performance["venue"],
                start=performance["start"],
                duration_minutes=performance["duration_minutes"],
                description=performance["description"],
                host=performance["host"],
                acts=performance["acts"]
            )

        elif kind == "workshop":
            p = Workshop(
                title=performance["title"],
                venue=performance["venue"],
                start=performance["start"],
                duration_minutes=performance["duration_minutes"],
                description=performance["description"],
                teacher=performance["teacher"],
                max_participants=performance["max_participants"],
                participants=performance["participants"]
            )

        else:
            raise ValueError(f"Unknown performance kind: {kind}")

        performances.append(p)
    venue_names = {
        slugify(venue.name): venue.name
        for venue in venues
    }

    results = []

    for perf in performances:
        roles = []

        if isinstance(perf, Solo):
            if slugify(perf.artist) == artist_slug:
                roles.append("solo")

        elif isinstance(perf, Lineup):
            if slugify(perf.host) == artist_slug:
                roles.append("host")

            for act in perf.acts:
                if slugify(act) == artist_slug:
                    roles.append("act")

        elif isinstance(perf, Workshop):
            if slugify(perf.teacher) == artist_slug:
                roles.append("teacher")

        for role in roles:
            results.append((perf, role))

    if not results:
        print(f"No artist '{artist_slug}'.")
        return

    print(artist_slug.replace("-", " ").title())

    for perf, role in sorted(results, key=lambda item: item[0].start):
        venue_name = venue_names.get(perf.venue, perf.venue)
        date_time = perf.start[:16].replace("T", " ")

        print(
            f"{date_time} | {venue_name} | "
            f"{perf.title} ({role})"
        )
def list_venues():
    venues = [
        Venue(v["name"], v["capacity"], v["address"])
        for v in json_connection.venues
    ]

    total_capacity = 0

    for venue in venues:
        print(
            f"{slugify(venue.name)}: {venue.name}, "
            f"{venue.capacity} seats"
        )
        total_capacity += venue.capacity

    print(f"Total: {total_capacity} seats")

def list_programme(day):
    venues = [
        Venue(v["name"], v["capacity"], v["address"])
        for v in json_connection.venues
    ]
    performances = []
    for performance in json_connection.performances:
            kind = performance["kind"]
    
            if kind == "solo":
                p = Solo(
                    title=performance["title"],
                    venue=performance["venue"],
                    start=performance["start"],
                    duration_minutes=performance["duration_minutes"],
                    description=performance["description"],
                    artist=performance["artist"],
                    min_age=performance["min_age"]
                )
    
            elif kind == "lineup":
                p = Lineup(
                    title=performance["title"],
                    venue=performance["venue"],
                    start=performance["start"],
                    duration_minutes=performance["duration_minutes"],
                    description=performance["description"],
                    host=performance["host"],
                    acts=performance["acts"]
                )
    
            elif kind == "workshop":
                p = Workshop(
                    title=performance["title"],
                    venue=performance["venue"],
                    start=performance["start"],
                    duration_minutes=performance["duration_minutes"],
                    description=performance["description"],
                    teacher=performance["teacher"],
                    max_participants=performance["max_participants"],
                    participants=performance["participants"]
                )
    
            else:
                raise ValueError(f"Unknown performance kind: {kind}")
    
            performances.append(p)
    venue_names = {
        slugify(venue.name): venue.name
        for venue in venues
    }

    daily_performances = [
        perf for perf in performances
        if perf.start[:10] == day
    ]

    if not daily_performances:
        print(f"No performances on '{day}'.")
        return

    print(f"Programme for {day}:")

    for perf in sorted(daily_performances, key=lambda p: p.start):
        time = perf.start[11:16]
        venue_name = venue_names.get(perf.venue, perf.venue)

        if isinstance(perf, Lineup):
            kind = "Lineup"
        elif isinstance(perf, Workshop):
            kind = "Workshop"
        elif isinstance(perf, Solo):
            kind = "Solo"
        else:
            kind = "Performance"

        print(
            f"{time} | {venue_name} | "
            f"{perf.title} ({kind})"
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

if __name__ == "__main__":
    main()
