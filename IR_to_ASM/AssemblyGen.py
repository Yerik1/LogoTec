import os
import subprocess
import shutil

class AssemblyGen:
    def __init__(self, llvm_ir_path="out/output.ll", asm_path="out/output.s"):
        self.ll_path = llvm_ir_path
        self.asm_path = asm_path

    def _find_llc(self):
        """Check if llc is in PATH or available."""
        llc_path = shutil.which("llc")
        if llc_path is None:
            raise FileNotFoundError(
                "LLVM 'llc' not found. Install LLVM and add it to your system PATH:\n"
                "https://llvm.org/releases/"
            )
        return llc_path

    def generate(self):
        """Generate assembly from LLVM IR."""
        os.makedirs(os.path.dirname(self.asm_path), exist_ok=True)
        llc_path = self._find_llc()
        subprocess.run([llc_path, "-filetype=asm", self.ll_path, "-o", self.asm_path], check=True)
        print(f"Assembly generated at {self.asm_path}")
        return self.asm_path
