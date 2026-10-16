"""Rebuild the standalone .ms embedded stdlib FBX reader."""
import base64
from pathlib import Path
import re


def rebuild():
    root = Path(__file__).resolve().parent
    source = (root / "fbx_inventory.py").read_bytes()
    compile(source, "fbx_inventory.py", "exec")
    target = root / "NPM_Texture_Linker.ms"
    text = target.read_text(encoding="utf-8-sig")
    payload = base64.b64encode(source).decode("ascii")
    text, count = re.subn(r'(?m)^AGR_NPMFbx_Payload = "[A-Za-z0-9+/=]*"$',
                          'AGR_NPMFbx_Payload = "' + payload + '"', text)
    if count != 1:
        raise ValueError("Expected exactly one embedded payload marker")
    target.write_text(text, encoding="utf-8-sig", newline="\n")


if __name__ == "__main__":
    rebuild()
