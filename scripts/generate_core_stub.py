from __future__ import annotations

from r3xa_api._stubgen import write_core_stub


def main() -> None:
    path = write_core_stub()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
