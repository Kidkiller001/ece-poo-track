from datetime import datetime, timedelta


class Performance:
    def __init__(
        self, title, venue, start,
        duration_minutes, description
    ):
        self.title = title
        self.venue = venue
        self.start = start
        self.duration_minutes = duration_minutes
        self.description = description

    @property
    def start_datetime(self):
        return datetime.fromisoformat(self.start)

    @property
    def end_datetime(self):
        return self.start_datetime + timedelta(
            minutes=self.duration_minutes
        )

    @property
    def kind(self):
        return self.__class__.__name__.lower()

    def __lt__(self, other):
        if not isinstance(other, Performance):
            return NotImplemented
        return (
            self.start_datetime,
            self.venue.name.casefold(),
        ) < (
            other.start_datetime,
            other.venue.name.casefold(),
        )

    def __str__(self):
        return (
            f"{self.start_datetime:%H:%M}-"
            f"{self.end_datetime:%H:%M} | "
            f"{self.venue.name} | "
            f"{self.title} ({self.kind})"
        )

    def to_dict(self):
        return {
            "title": self.title,
            "venue": self.venue.slug,
            "start": self.start,
            "duration_minutes": self.duration_minutes,
            "description": self.description,
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(title={self.title!r})"
