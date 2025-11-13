import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)

from core.file_parser import FileParser


def main() -> None:
    file_path = Path(__file__).resolve().parents[1] / "tests" / "input" / "sample_invoic5.xlsx"
    print("--- START PARSE ---")
    parser = FileParser()
    result = parser.parse_file(file_path)
    print("--- END PARSE ---")

    if isinstance(result, dict):
        selected = result.get("selected_sheet") or result
        if isinstance(selected, dict):
            print("Selected sheet:", selected.get("sheet_name"))
            print("Header row:", selected.get("header_row"))
            families = selected.get("families") or []
            print("Families:", len(families))
        else:
            print("Result type:", type(selected))
    else:
        print("Result type:", type(result))


if __name__ == "__main__":
    main()







