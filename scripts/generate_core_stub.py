from __future__ import annotations

from r3xa_api._stubgen import write_core_stub, write_package_stub


def main() -> None:
    print(f"Wrote {write_core_stub()}")
    print(f"Wrote {write_package_stub()}")


if __name__ == "__main__":
    main()
