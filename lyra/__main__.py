import sys


def main() -> None:
    if "--cli" in sys.argv:
        from .cli import run
        try:
            run()
        except KeyboardInterrupt:
            pass
    elif "--stats" in sys.argv:
        _print_stats()
    elif "--daemon" in sys.argv:
        from .daemon import run as run_daemon
        run_daemon()
    else:
        from .app import run_gui
        run_gui()


def _print_stats() -> None:
    from . import stats as s

    totals = s.total_stats()
    if not totals or totals["total_plays"] == 0:
        print("No play history yet. Start listening and come back!")
        return

    W = 48
    print()
    print("─" * W)
    print("  Lyra Listening Stats")
    print("─" * W)
    print(f"  Plays          {totals['total_plays']:>6}")
    print(f"  Listening time {totals['total_hours']:>5.1f} h")
    print(f"  Unique artists {totals['unique_artists']:>6}")
    print(f"  Unique genres  {totals['unique_genres']:>6}")

    artists = s.top_artists(10)
    if artists:
        print()
        print("  Top Artists")
        print("  " + "─" * (W - 2))
        for artist, cnt, hrs in artists:
            print(f"  {artist:<28} {cnt:>4} plays  {hrs:.1f} h")

    genres = s.genre_distribution()
    if genres:
        print()
        print("  Genre Distribution")
        print("  " + "─" * (W - 2))
        total = totals["total_plays"]
        for genre, cnt in genres:
            bar = "█" * min(20, round(cnt / total * 20))
            print(f"  {genre:<22} {bar:<20} {cnt:>4}")

    print("─" * W)
    print()


if __name__ == "__main__":
    main()
