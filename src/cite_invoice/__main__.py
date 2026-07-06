from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import validate_and_convert
from .models import EngineResult


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CITE XML invoices and convert them to JSON.")
    parser.add_argument("input", type=Path, help="CITE XML file or folder of XML files.")
    parser.add_argument("--out", "-o", type=Path, help="Output JSON file for one input, or output folder for many.")
    args = parser.parse_args()

    input_path: Path = args.input
    output_path: Path | None = args.out

    if not input_path.exists():
        parser.error(f"Input path does not exist: {input_path}")

    files = _input_files(input_path)
    if not files:
        parser.error(f"No .xml files found in {input_path}")

    passed = 0
    failed = 0

    for file_path in files:
        result = _process_file(file_path)
        destination = _destination_for(file_path, input_path, output_path)

        if result.is_valid:
            assert result.json_document is not None
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result.json_document, indent=2) + "\n", encoding="utf-8")
            print(f"PASS {file_path} -> {destination}")
            passed += 1
        else:
            print(f"FAIL {file_path}")
            for issue in result.issues:
                print(f"  {issue.format()}")
            failed += 1

    print()
    print(f"Summary: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


def _process_file(path: Path) -> EngineResult:
    return validate_and_convert(path.read_text(encoding="utf-8"))


def _input_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]

    return sorted(child for child in path.iterdir() if child.is_file() and child.suffix.lower() == ".xml")


def _destination_for(file_path: Path, input_path: Path, output_path: Path | None) -> Path:
    if input_path.is_file():
        if output_path is None:
            return file_path.with_suffix(".out.json")
        if output_path.suffix:
            return output_path
        return output_path / file_path.with_suffix(".json").name

    output_dir = output_path or Path("converted-json")
    return output_dir / file_path.with_suffix(".json").name


if __name__ == "__main__":
    raise SystemExit(main())
