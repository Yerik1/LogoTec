import subprocess
import os

class AssemblyGen:
    def __init__(self, ll_path="out/output.ll", asm_path="out/output.s"):
        self.ll_path = ll_path
        self.asm_path = asm_path

    def generate(self):
        """Convert LLVM IR (.ll) to assembly (.s) using llc."""
        if not os.path.exists(self.ll_path):
            raise FileNotFoundError(f"LLVM IR file not found: {self.ll_path}")
        os.makedirs(os.path.dirname(self.asm_path), exist_ok=True)
        subprocess.run(["llc", "-filetype=asm", self.ll_path, "-o", self.asm_path], check=True)
        return self.asm_path

    def link(self, output_exe="out/output"):
        """Optional: Link .s into an executable using clang."""
        subprocess.run(["clang", self.asm_path, "-o", output_exe], check=True)
        return output_exe
