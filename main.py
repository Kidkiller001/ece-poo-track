import sys
from festival import (
    list_venues,
    list_artist_performances,
    list_programme,
    list_now,
    add_performance,
    cancel_performance,)
def main():
    
    command = sys.argv[1] if len(sys.argv) > 1 else None

    if command == "venues":
        list_venues()
    elif command == "artist" and len(sys.argv) >= 3:
        artist_slug = sys.argv[2].lower()
        list_artist_performances(
            artist_slug,
        )
    elif command == "programme" and len(sys.argv) >= 3:
        day = sys.argv[2]
        list_programme(day)
    elif command == "now" and len(sys.argv) >= 3:
        list_now(
            sys.argv[2]
        )
    elif command == "add" and len(sys.argv) >= 2:
        add_performance()
    elif command == "cancel" and len(sys.argv) >= 3:
        performance_id_to_cancel = sys.argv[2]
        cancel_performance(performance_id_to_cancel)

if __name__ == "__main__":
    main()
