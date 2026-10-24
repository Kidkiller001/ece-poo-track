import json
from venue import Venue
from performance import Performance
from lineup import Lineup
from workshop import Workshop
from solo import Solo
def main():
    with open("./data/festival.json", "r") as f:
        data = json.load(f)
    venues = []
    performances = []
    for venue in data["venues"]:
        v= Venue(venue["name"], venue["capacity"], venue["address"])
        venues.append(v)
    for performance in data["performances"]:
        if performance["kind"] == "solo":
            p = Solo(
                title=performance["title"],
                venue=performance["venue"],
                start=performance["start"],
                duration_minutes=performance["duration_minutes"],
                description=performance["description"],
                artist=performance["artist"],
                min_age=performance["min_age"]
            )
        elif performance["kind"] == "lineup":
            p = Lineup(
                title=performance["title"],
                venue=performance["venue"],
                start=performance["start"],
                duration_minutes=performance["duration_minutes"],
                description=performance["description"],
                host=performance["host"],
                acts=performance["acts"]
            )
        elif performance["kind"] == "workshop":
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
        print(p)
        performances.append(p)
    N_solo = sum(1 for p in performances if isinstance(p, Performance) and not isinstance(p, Lineup) and not isinstance(p, Workshop))
    N_lineup = sum(1 for p in performances if isinstance(p, Lineup))
    N_workshop = sum(1 for p in performances if isinstance(p, Workshop))

    print(f"lineup:{N_lineup}\n solo: {N_solo}\n workshop: {N_workshop}")
    for v in venues:
        print(v)
    

if __name__ == "__main__":
    main()
