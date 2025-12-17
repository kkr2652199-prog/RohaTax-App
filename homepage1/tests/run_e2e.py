import os
import sys
import json
import locale

# Force UTF-8 for reliable Korean output on Windows
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")  # Python 3.7+
except Exception:
    pass

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.conversion_engine import ConversionEngine


def run(sample_path: str) -> dict:
    engine = ConversionEngine()
    supplier_info = {
        "company_name": "테스트공급자",
        "business_number": "123-45-67890",
        "representative_name": "홍길동",
        "address": "서울시 테스트로 1",
        "business_type": "도소매업",
        "business_category": "기타",
        "email": "test@supplier.com",
    }

    result = engine.convert_file(
        uploaded_file_path=sample_path,
        supplier_info=supplier_info,
        template_id="hometax_official",
        industry_type="delivery",
        guidelines={},
        issue_date=None,
        user_info={"business_number": "1234567890", "company_name": "테스트공급자"},
    )
    return result


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(__file__))
    sample = os.path.join(base, "tests", "input", "sample_invoice2.xlsx")
    res = run(sample)
    # Write clean JSON to file to avoid mixed logs in stdout
    out_path = os.path.join(base, "tests", "e2e_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(out_path)


