import json
from venue import Venue
from performance import Performance
from lineup import Lineup
from workshop import Workshop
from solo import Solo
from collections import Counter
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
        performances.append(p)
    N_solo = sum(1 for p in performances if isinstance(p, Performance) and not isinstance(p, Lineup) and not isinstance(p, Workshop))
    N_lineup = sum(1 for p in performances if isinstance(p, Lineup))
    N_workshop = sum(1 for p in performances if isinstance(p, Workshop))
    le_kiosque_performances = []
    print(f"Performances at Le Kiosque:\n")
    for perf in performances:
        if perf.venue == "le-kiosque":
            le_kiosque_performances.append(perf)
            print(f"{perf.start} {perf.title}")
    
    print(f"lineup:{N_lineup}\nsolo: {N_solo}\nworkshop: {N_workshop}")
    for v in venues:
        print(v)
    
    longest_performance = max(performances, key=lambda p: p.duration_minutes)
    print(f"\nLongest {longest_performance.title} ({longest_performance.duration_minutes} mins)")

    for perf in performances:
            if isinstance(perf, Workshop):
                print(f"{perf.title} on {perf.start}: {len(perf.participants)}/{perf.max_participants} registered")

    artist_counts = Counter()

    for perf in performances:
        if isinstance(perf, Lineup):
            artist_counts[perf.host] += 1
            artist_counts.update(perf.acts)

        elif isinstance(perf, Workshop):
            artist_counts[perf.teacher] += 1

        elif isinstance(perf, Performance):
            artist_counts[perf.artist] += 1

    if artist_counts:
        max_count = max(artist_counts.values())

        most_frequent_artists = [
            artist
            for artist, count in artist_counts.items()
            if count == max_count
        ]

        print(f"Artists on stage {max_count}: {', '.join(most_frequent_artists)}")

            
    
if __name__ == "__main__":
    main()
