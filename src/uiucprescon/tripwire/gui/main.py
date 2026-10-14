"""Run the speedwagon GUI."""


def main():
    """Run the speedwagon GUI."""
    try:
        from uiucprescon.tripwire.gui.bootstrap_speedwagon import (
            run_speedwagon
        )
        run_speedwagon()
    except ImportError as e:
        print(f"Unable to load speedwagon: {e}")


if __name__ == '__main__':
    main()
