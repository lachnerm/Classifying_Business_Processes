import argparse
import json
from itertools import product
from pathlib import Path

import yaml

# Unicode mapping used by the AR-matrix export
SYMBOL_MAP = {
    "≺": "<",
    "≻": ">",
    "⇔": "<=>",
    "⇎": "</=>",
}

def normalize_symbol(s, remove_t=False):
    """
    Normalize a single temporal/existential symbol:
      - optionally remove 't' for temporal dependencies
      - replace unicode symbols by ASCII equivalents
      - return '-' if empty after cleaning
    """
    s = (s or "").strip()
    if remove_t:
        s = s.replace("t", "")
    for old, new in SYMBOL_MAP.items():
        s = s.replace(old, new)
    return s if s else "-"


def convert_yaml_to_json(yaml_path, out_path=None):
    """
    Convert an activity-relationship matrix exported as YAML into the JSON
    format expected by the classifier.

    Rules:
      - Activities:
          * infer from metadata.activities
      - Initialize full |A|x|A| matrix:
          * (a,a) = "-,-"
      - For each dependency (a -> b):
          * temporal  = normalized symbol (remove 't'), or '-'
          * existential = normalized symbol, or '-'
          * relation = "{temporal},{existential}"
    """
    yaml_path = Path(yaml_path)
    if out_path is None:
        out_path = yaml_path.with_suffix(".json")
    out_path = Path(out_path)

    # Load YAML
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    deps = data.get("dependencies", []) or []

    # Collect activities
    activities = data.get("metadata", {}).get("activities", [])

    # Initialize matrix with defaults
    matrix = {a1: {} for a1 in activities}
    for a1, a2 in product(activities, repeat=2):
        matrix[a1][a2] = "-,-"

    # Apply dependencies
    for d in deps:
        a = d.get("from")
        b = d.get("to")
        if a not in matrix or b not in matrix[a]:
            continue

        temporal = normalize_symbol(d.get("temporal", {}).get("symbol", ""), remove_t=True)
        existential = normalize_symbol(d.get("existential", {}).get("symbol", ""), remove_t=False)

        matrix[a][b] = f"{temporal},{existential}"

    # Write JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert AR-matrix YAML to classifier-ready JSON."
    )
    parser.add_argument("yaml", help="Path to YAML file exported from the AR-matrix discovery tool.")
    parser.add_argument(
        "--out",
        help="Optional output JSON path. Defaults to same name/location with '.json' extension.",
        default=None,
    )
    args = parser.parse_args()

    out_path = convert_yaml_to_json(args.yaml, args.out)
    print(f"✅ JSON successfully written to: {out_path}")


if __name__ == "__main__":
    main()
