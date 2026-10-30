
from datetime import date, datetime

from venue import Venue
from artist import Artist
from solo import Solo
from lineup import Lineup
from workshop import Workshop


class FestivalRepository:
    def __init__(self, json_connection):
        self.json_connection = json_connection

        # Load objects in dependency order:
        # venues first, then artists, then performances.
        self._venues = self._load_venues()
        self._artists = self._load_artists()
        self._performances = self._load_performances()

    def _load_venues(self):
        return [
            Venue(
                v["name"],
                v["capacity"],
                v["address"]
            )
            for v in self.json_connection.venues
        ]

    def _load_artists(self):
        artists = [
            Artist(
                name=item["name"],
                bio=item["bio"],
                photo_url=item["photo_url"]
            )
            for item in self.json_connection.data["artists"]
        ]

        return {
            artist.slug: artist
            for artist in artists
        }

    def _load_performances(self):
        performances = []

        # Build lookup dictionaries to resolve relationships.
        venues = {
            venue.slug: venue
            for venue in self._venues
        }

        artists = self._artists

        for item in self.json_connection.performances:
            kind = item["kind"]

            # Shared attributes for all performance types.
            common_data = {
                "title": item["title"],
                "venue": venues[item["venue"]],
                "start": item["start"],
                "duration_minutes": item["duration_minutes"],
                "description": item["description"],
            }

            if kind == "solo":
                performance = Solo(
                    **common_data,
                    artist=artists[item["artist"]],
                    min_age=item["min_age"]
                )

            elif kind == "lineup":
                performance = Lineup(
                    **common_data,
                    host=artists[item["host"]],
                    acts=[
                        artists[act]
                        for act in item["acts"]
                    ]
                )

            elif kind == "workshop":
                performance = Workshop(
                    **common_data,
                    teacher=artists[item["teacher"]],
                    max_participants=item["max_participants"],
                    participants=item["participants"]
                )

            else:
                raise ValueError(
                    f"Unknown performance kind: {kind}"
                )

            performances.append(performance)

        return performances

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def venues(self):
        return self._venues

    @property
    def artists(self):
        return self._artists

    @property
    def performances(self):
        return self._performances

    # --------------------------------------------------
    # Individual object retrieval
    # --------------------------------------------------

    def get_venue(self, slug):
        return next(
            (
                venue
                for venue in self._venues
                if venue.slug == slug
            ),
            None
        )

    def get_artist(self, slug):
        return self._artists.get(slug)

    def get_performance(self, performance_id):
        """
        Retrieve a performance using its generated ID.

        ID format:
        venue-slug-YYYY-MM-DD-HHMM
        """

        for performance in self._performances:
            start = datetime.fromisoformat(performance.start)

            current_id = (
                f"{performance.venue.slug}-"
                f"{start:%Y-%m-%d-%H%M}"
            )

            if current_id == performance_id:
                return performance

        return None

    # --------------------------------------------------
    # Performance filtering
    # --------------------------------------------------

    def list_performances(
        self,
        day: date | None = None,
        venue: str | None = None
    ):
        results = self._performances

        # Filter by calendar date.
        if day is not None:
            results = [
                performance
                for performance in results
                if datetime.fromisoformat(
                    performance.start
                ).date() == day
            ]

        # Filter by venue slug.
        if venue is not None:
            results = [
                performance
                for performance in results
                if performance.venue.slug == venue
            ]

        return results

    # --------------------------------------------------
    # Artist-related performances
    # --------------------------------------------------

    def performances_for_artist(self, slug):
        artist = self.get_artist(slug)

        if artist is None:
            return []

        return [
            performance
            for performance in self._performances
            if (
                getattr(performance, "artist", None) == artist
                or getattr(performance, "host", None) == artist
                or getattr(performance, "teacher", None) == artist
                or artist in getattr(performance, "acts", [])
            )
        ]
