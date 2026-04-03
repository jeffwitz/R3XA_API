from pathlib import Path

from r3xa_api import Registry


def main() -> None:
    root = Path(__file__).parents[2]
    registry = Registry(root / "registry")
    output_path = root / "examples" / "artifacts" / "registry_camera_merged.json"

    camera_keys = registry.list(kind="data_sources/camera")
    print("Available camera registry entries:")
    for tree_path in camera_keys:
        print(f"- {tree_path}")

    merged_camera = registry.get_item("data_sources/camera/avt_dolphin_f145b").merge(
        id="ds_cam_registry_demo",
        title="Registry camera clone",
        description="Merged from registry discovery example",
    )
    saved_path = merged_camera.save(output_path)

    print(f"Merged camera saved to: {saved_path}")


if __name__ == "__main__":
    main()
