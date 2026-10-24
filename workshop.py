from performance import Performance

class Workshop(Performance):
    def __init__(
        self, title, venue, start, duration_minutes,
        description, teacher, max_participants,
        participants
    ):
        super().__init__(
            title, venue, start,
            duration_minutes, description
        )
        self.teacher = teacher
        self.max_participants = max_participants
        self.participants = participants