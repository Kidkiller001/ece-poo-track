from performance import Performance

class Solo(Performance):
    def __init__(
        self, title, venue, start, duration_minutes,
        description, artist, min_age=0
    ):
        super().__init__(
            title, venue, start,
            duration_minutes, description
        )
        self.artist = artist
        self.min_age = min_age
    def to_dict(self):
        data = super().to_dict()

        data.update({
            "kind": "solo",
            "artist": self.artist.slug,
            "min_age": self.min_age,
        })

        return data