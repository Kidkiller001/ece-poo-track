from performance import Performance

class Lineup(Performance):
    def __init__(
        self, title, venue, start, duration_minutes,
        description, host, acts
    ):
        super().__init__(
            title, venue, start,
            duration_minutes, description
        )
        self.host = host
        self.acts = acts
    def to_dict(self):
        data = super().to_dict()

        data.update({
            "kind": "lineup",
            "host": self.host.slug,
            "acts": [artist.slug for artist in self.acts],
        })

        return data