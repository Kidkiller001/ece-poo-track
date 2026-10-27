
from venue import Venue
from solo import Solo
from lineup import Lineup
from workshop import Workshop


class FestivalRepository:
    def __init__(self, json_connection):
        self.json_connection = json_connection
        self._venues = self._load_venues()
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

    def _load_performances(self):
        performances = []

        for item in self.json_connection.performances:
            kind = item["kind"]

            if kind == "solo":
                performance = Solo(
                    title=item["title"],
                    venue=item["venue"],
                    start=item["start"],
                    duration_minutes=item["duration_minutes"],
                    description=item["description"],
                    artist=item["artist"],
                    min_age=item["min_age"]
                )

            elif kind == "lineup":
                performance = Lineup(
                    title=item["title"],
                    venue=item["venue"],
                    start=item["start"],
                    duration_minutes=item["duration_minutes"],
                    description=item["description"],
                    host=item["host"],
                    acts=item["acts"]
                )

            elif kind == "workshop":
                performance = Workshop(
                    title=item["title"],
                    venue=item["venue"],
                    start=item["start"],
                    duration_minutes=item["duration_minutes"],
                    description=item["description"],
                    teacher=item["teacher"],
                    max_participants=item["max_participants"],
                    participants=item["participants"]
                )

            else:
                raise ValueError(
                    f"Unknown performance kind: {kind}"
                )

            performances.append(performance)

        return performances

    @property
    def venues(self):
        return self._venues

    @property
    def performances(self):
        return self._performances
