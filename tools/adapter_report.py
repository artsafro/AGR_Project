"""Validate an existing report; print bounded summary, never the mesh/log payload."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dt_ai.core.adapter_report import AdapterReport
from dt_ai.core.io import read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = AdapterReport.model_validate(read_json(args.report.read_bytes()))
    print(json.dumps({**report.summary(), "full_report": str(args.report.resolve())},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()

