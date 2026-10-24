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