from pathlib import Path

from r3xa_api import R3XAFile


def main() -> None:
    root = Path(__file__).parents[2]
    input_path = root / "examples" / "artifacts" / "dic_pipeline.json"
    output_path = root / "examples" / "artifacts" / "dic_pipeline_loaded.json"

    r3xa = R3XAFile.load(input_path)
    r3xa.set_header(
        title="Open-hole tensile test with DIC (loaded example)",
        repository="https://example.org/r3xa-api/demo",
    )
    saved_path = r3xa.save(output_path)

    print(f"Loaded: {input_path}")
    print(f"Saved: {saved_path}")


if __name__ == "__main__":
    main()
