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

    def __repr__(self):
        return f"{self.__class__.__name__}(title={self.title!r})"