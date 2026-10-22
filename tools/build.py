import json
import sys
import tarfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "print-buddy-streamer"


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    for tier, spec in json.loads((ROOT / "tiers.json").read_text()).items():
        path = out / f"{NAME}-{tier}.tar.gz"
        with tarfile.open(path, "w:gz") as tar:
            for f in spec["files"]:
                tar.add(ROOT / f, arcname=f"{NAME}/{f}", filter=lambda t: None if "__pycache__" in t.name else t)
            data = tier.encode()
            info = tarfile.TarInfo(f"{NAME}/streamer/TIER")
            info.size = len(data)
            tar.addfile(info, BytesIO(data))
        print(path)


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "dist"))
