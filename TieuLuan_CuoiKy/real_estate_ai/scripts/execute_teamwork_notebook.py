"""Execute the submission in a fresh kernel and check the saved outputs."""
import base64
import json
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "TeamWork_PP_Nhom8.ipynb"
QA = PROJECT / ".buildtmp" / "notebook_qa"
QA.mkdir(parents=True, exist_ok=True)
runtime = PROJECT / ".buildtmp" / "jupyter_runtime"
runtime.mkdir(parents=True, exist_ok=True)
os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime)
os.environ["IPYTHONDIR"] = str(PROJECT / ".buildtmp" / "ipython")
os.environ["MPLCONFIGDIR"] = str(PROJECT / ".buildtmp" / "matplotlib")


def progress(cell, cell_index, **kwargs):
    if cell.cell_type == "code":
        print(f"Executing code cell at index {cell_index}", flush=True)


nb = nbformat.read(NOTEBOOK, as_version=4)
km = KernelManager(kernel_name="python3")
km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
client = NotebookClient(
    nb, km=km, timeout=300, allow_errors=False,
    resources={"metadata": {"path": str(PROJECT.parent)}},
    on_cell_start=progress,
)
client.execute()
nbformat.validate(nb)
code_cells = [cell for cell in nb.cells if cell.cell_type == "code"]
assert all(cell.execution_count is not None for cell in code_cells)
assert [cell.execution_count for cell in code_cells] == list(range(1, len(code_cells) + 1))
assert not any(out.output_type == "error" for cell in code_cells for out in cell.outputs)

figures = []
texts = []
for index, cell in enumerate(nb.cells):
    for out in cell.get("outputs", []):
        data = out.get("data", {})
        if "image/png" in data:
            path = QA / f"figure_{len(figures) + 1}.png"
            path.write_bytes(base64.b64decode(data["image/png"]))
            figures.append(str(path))
        if "text/plain" in data:
            texts.append(f"CELL {index}\n{data['text/plain']}")
        if "text/markdown" in data:
            texts.append(f"CELL {index}\n{data['text/markdown']}")
        if out.output_type == "stream":
            texts.append(f"CELL {index}\n{out.text}")
assert len(figures) >= 3, "Missing required EDA plots"
nbformat.write(nb, NOTEBOOK)
(QA / "outputs.txt").write_text("\n\n".join(texts), encoding="utf-8")
summary = {"notebook": str(NOTEBOOK), "code_cells": len(code_cells), "figures": figures, "errors": 0}
(QA / "verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
