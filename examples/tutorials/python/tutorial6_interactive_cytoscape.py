"""Open an existing R3XA document and export its interactive graph."""

from pathlib import Path

from r3xa_api import R3XAFile


repo_root = Path(__file__).resolve().parents[3]
source = repo_root / "tests" / "fixtures" / "documents" / "essai-torsion.json"
artifacts = repo_root / "artifacts" / "examples" / "tutorials"
artifacts.mkdir(parents=True, exist_ok=True)

document = R3XAFile.load(source)
document.validate()
graph_path = document.plot(
    artifacts / "torsion_cytoscape.html",
    backend="cytoscape",
    include_description=False,
)

print(f"Loaded: {document.title} ({len(document.data_sources)} sources, {len(document.data_sets)} sets)")
print(f"Interactive graph: {graph_path.relative_to(repo_root)}")
