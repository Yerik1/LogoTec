# build_native.py
import os, shutil, subprocess
from pathlib import Path

CLANG = shutil.which("clang") or shutil.which("gcc")
if not CLANG:
    raise RuntimeError("No encontré clang/gcc en PATH")

def build_and_link(asm_path: str, out_dir="out", exe_name="turtle"):
    package = Path(__file__).parent.resolve()
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    asm = Path(asm_path)
    if not asm.exists():
        raise FileNotFoundError(asm_path)

    obj        = out / (asm.stem + ".o")
    runtime_c  = package / "runtime.c"
    server_py  = package / "drawing.py"
    exe        = out / (exe_name + (".exe" if os.name=="nt" else ""))

    assert runtime_c.exists(), "Falta runtime.c"
    assert server_py.exists(), "Falta drawing.py"

    # 1) .s -> .o
    subprocess.run([CLANG, "-c", str(asm), "-o", str(obj)], check=True)

    # 2) runtime.c -> runtime.o
    runtime_o = out / "runtime.o"
    subprocess.run([CLANG, "-c", str(runtime_c), "-o", str(runtime_o)], check=True)

    # 3) link -> exe
    subprocess.run([CLANG, str(obj), str(runtime_o), "-o", str(exe)], check=True)

    # 4) COPIAR drawing.py (o turtle_server.py) a out/
    server_src = Path(__file__).parent / "drawing.py"  # o "turtle_server.py"
    server_dst = out / server_src.name
    shutil.copyfile(server_src, server_dst)
    return str(exe)

