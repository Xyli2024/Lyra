import sys


def main() -> None:
    if "--cli" in sys.argv:
        from .cli import run
        try:
            run()
        except KeyboardInterrupt:
            pass
    else:
        from .app import run_gui
        run_gui()


if __name__ == "__main__":
    main()
