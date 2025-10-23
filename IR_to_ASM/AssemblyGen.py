import os
import subprocess

class AssemblyGen:
    def __init__(self, ir_path="out/output.ll", asm_path="out/output.s"):
        self.ir_path = ir_path
        self.asm_path = asm_path

    def generate(self):
        # Ensure input IR exists
        if not os.path.exists(self.ir_path):
            raise FileNotFoundError(f"IR file not found: {self.ir_path}")

        # Create output directory if needed
        os.makedirs(os.path.dirname(self.asm_path), exist_ok=True)

        # Run llc to produce assembly
        cmd = ["llc", self.ir_path, "-o", self.asm_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Assembly generation failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            )

        print(f"Assembly written to: {self.asm_path}")
        return self.asm_path
