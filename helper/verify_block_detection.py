import os
import sys
import pprint

# Add parent directory to Python path so utils.py can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_relationships
from block_detection import detect_blocks, build_super_blocks

# Known development files (kept for convenience/documentation)
DEV_FILES = [
    "data_development/data/Log01_structured.json",
    "data_development/data/Log02_semiStructured.json",
    "data_development/data/Log03_looselyStructured.json",
    "data_development/data/Log04_structured.json",
    "data_development/data/Log05_structured.json",
    "data_development/data/Log06_semiStructured.json",
    "data_development/data/Log07_semiStructured.json",
    "data_development/data/Log08_looselyStructured.json",
    "data_development/data/Log09_unstructured.json",
    "data_development/data/Log10_semiStructured.json",
    "data_development/data/Log11_looselyStructured.json",
    "data_development/data/Log12_structured.json",
    "data_development/data/Log13_semiStructured.json",
    "data_development/data/Log14_looselyStructured.json",
    "data_development/data/Log15_structured.json",
    "data_development/data/Log16_looselyStructured.json",
    "data_development/data/Log17_semiStructured.json",
    "data_development/data/Log18_structured.json",
    "data_development/data/Log20_semiStructured.json",
    "data_development/data/Log21_looselyStructured.json",
    "data_development/data/Log22_looselyStructured.json",
    "data_development/data/Log23_looselyStructured.json",
    "data_development/data/Log24_unstructured.json",
    "data_development/data/Log25_structured.json",
    "data_development/data/Log26_structured.json",
    "data_development/data/Log27_semiStructured.json",
    "data_development/data/Log28_structured.json"
]

# Order-invariant expected outputs for development files
EXPECTED = {
    "data_development/data/Log01_structured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": ["c", ("d", "e")], "block_type": "XOR", "end": "f",
             "nested": [
                 {"activities": ["d", "e"], "block_type": "PAR", "end": None, "nested": [], "start": "b"}
             ], "start": "b"},
        ],
        
        "super": [
            {"activities": ["b", "c", "d", "e"], "end": "f", "start": "a"}
        ],
    },
    "data_development/data/Log02_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": ["d", "e"], "block_type": "XOR", "end": None, "nested": [], "start": "c"},
        ],
        
        "super": [
            {"activities": [], "end": "b", "start": "a"},
            {"activities": ["d", "e"], "end": None, "start": "c"},
        ],
    },
    "data_development/data/Log03_looselyStructured.json": {
        "blocks": [
            {"activities": ["a", "e"], "block_type": "PAR", "end": None, "nested": [], "start": None},
            {"activities": ["d", ("b", "c")], "block_type": "XOR", "end": None, "nested": [], "start": None}
        ],
        
        "super": [
            {"activities": ["a", "e"], "end": None, "start": None},
            {"activities": ["b", "c", "d"], "end": None, "start": None}
        ],
    },
    "data_development/data/Log04_structured.json": {
        "blocks": [
            {"activities": ["e", "f"], "block_type": "XOR", "end": None, "nested": [], "start": "d"},
            {"activities": ["b", "c"], "block_type": "PAR", "end": "d", "nested": [], "start": "a"},
        ],
        
        "super": [
            {"activities": ["b", "c", "d", "e", "f"], "end": None, "start": "a"},
        ],
    },
    "data_development/data/Log05_structured.json": {
        "blocks": [
            {"activities": ["f", ("a", "c")], "block_type": "XOR", "end": None, "nested": [], "start": None},
            {"activities": ["b", "e"], "block_type": "XOR", "end": None, "nested": [], "start": None},
            {"activities": ["a", ("d", "f")], "block_type": "XOR", "end": None, "nested": [], "start": None}
        ],
        "super": [
            {"activities": ["a", "b", "c", "d", "e", "f"], "end": None, "start": None},
        ],
    },
    "data_development/data/Log06_semiStructured.json": {
        "blocks": [
            {"activities": ["b"], "block_type": "SEQUENCE", "end": "c", "nested": [], "start": "a"},
            {"activities": ["e", "f"], "block_type": "PAR", "end": None, "nested": [], "start": "d"},
        ],
        
        "super": [
            {"activities": ["b"], "end": "c", "start": "a"},
            {"activities": ["e", "f"], "end": None, "start": "d"},
        ],
    },
    "data_development/data/Log07_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": [], "block_type": "SEQUENCE", "end": "i", "nested": [], "start": "h"},
            {"activities": ["e", "f"], "block_type": "XOR", "end": "g", "nested": [], "start": "d"}
        ],
        
        "super": [
            {"activities": [], "end": "b", "start": "a"},
            {"activities": [], "end": "i", "start": "h"},
            {"activities": ["e", "f"], "end": "g", "start": "d"}
        ]
    },
    "data_development/data/Log08_looselyStructured.json": {"blocks": [],  "super": []},
    "data_development/data/Log09_unstructured.json": {
        "blocks": [{"activities": ["a", "b", "c"], "block_type": "PAR", "end": None, "nested": [], "start": None}],
        
        "super": [{"activities": ["a", "b", "c"], "end": None, "start": None}],
    },
    "data_development/data/Log10_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "g", "nested": [], "start": "f"},
            {"activities": ["b"], "block_type": "SEQUENCE", "end": "c", "nested": [], "start": "a"},
        ],
        
        "super": [
            {"activities": [], "end": "g", "start": "f"},
            {"activities": ["b"], "end": "c", "start": "a"},
        ],
    },
    "data_development/data/Log11_looselyStructured.json": {
        "blocks": [{"activities": ["d", "e"], "block_type": "PAR", "end": None, "nested": [], "start": None}],
        
        "super": [{"activities": ["d", "e"], "end": None, "start": None}],
    },
    "data_development/data/Log12_structured.json": {
        "blocks": [
            {
                "activities": [("b", "e", "f", "h"), ("c", "g"), ("d", "g")],
                "block_type": "XOR",
                "end": None,
                "nested": [{"activities": ["f", ("e", "h")], "block_type": "PAR", "end": None, "nested": [], "start": "b"}],
                "start": "a",
            },
        ],
        
        "super": [{"activities": ["b", "c", "d", "e", "f", "g", "h"], "end": None, "start": "a"}],
    },
    "data_development/data/Log13_semiStructured.json": {
        "blocks": [
            {"activities": ["g", "h"], "block_type": "PAR", "end": None, "nested": [], "start": None},
            {"activities": [("c", "i", "j"), ("d", "e", "f")], "block_type": "XOR", "end": None, "nested": [], "start": None},
        ],
        
        "super": [
            {"activities": ["c", "d", "e", "f", "i", "j"], "end": None, "start": None},
            {"activities": ["g", "h"], "end": None, "start": None},
        ],
    },
    "data_development/data/Log14_looselyStructured.json": {
        "blocks": [{"activities": ["becomeHoly", "curse"], "block_type": "XOR", "end": None, "nested": [], "start": None}],
        
        "super": [{"activities": ["becomeHoly", "curse"], "end": None, "start": None}],
    },
    "data_development/data/Log15_structured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "g", "nested": [], "start": "f"},
            {
                "activities": ["e", ("b", "c", "d")],
                "block_type": "XOR",
                "end": "f",
                "nested": [{"activities": ["b", "c", "d"], "block_type": "PAR", "end": None, "nested": [], "start": "a"}],
                "start": "a",
            },
            {"activities": ["h"], "block_type": "OPTIONAL", "end": "i", "nested": [], "start": "g"},
        ],
        "super": [{"activities": ["b", "c", "d", "e", "f", "g", "h"], "end": "i", "start": "a"}],
    },
    "data_development/data/Log16_looselyStructured.json": {
        "blocks": [{"activities": ["a", "b"], "block_type": "PAR", "end": None, "nested": [], "start": None}],
        
        "super": [{"activities": ["a", "b"], "end": None, "start": None}],
    },
    "data_development/data/Log17_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": ["c", "d"], "block_type": "PAR", "end": "e", "nested": [], "start": "b"},
        ],
        "super": [{"activities": ["b", "c", "d"], "end": "e", "start": "a"}],
    },
    "data_development/data/Log18_structured.json": {
        "blocks": [{"activities": [("a", "b"), ("c", "d")], "block_type": "PAR", "end": None, "nested": [], "start": None}],
        
        "super": [{"activities": ["a", "b", "c", "d"], "end": None, "start": None}],
    },
    "data_development/data/Log19_structured.json": {
        "blocks": [
            {"activities": ["a", "b"], "block_type": "XOR", "end": None, "nested": [], "start": None},
            {"activities": ["d", "e"], "block_type": "PAR", "end": None, "nested": [], "start": None},
        ],
        
        "super": [
            {"activities": ["a", "b"], "end": None, "start": None},
            {"activities": ["d", "e"], "end": None, "start": None},
        ],
    },
    "data_development/data/Log20_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "e", "nested": [], "start": "d"},
            {"activities": ["b", "c"], "block_type": "XOR", "end": None, "nested": [], "start": "a"},
        ],
        
        "super": [
            {"activities": [], "end": "e", "start": "d"},
            {"activities": ["b", "c"], "end": None, "start": "a"},
        ],
    },
    "data_development/data/Log21_looselyStructured.json": {
        "blocks": [{"activities": ["b", "c"], "block_type": "PAR", "end": None, "nested": [], "start": None}],
        
        "super": [{"activities": ["b", "c"], "end": None, "start": None}],
    },
    "data_development/data/Log22_looselyStructured.json": {
        "blocks": [
            {"activities": ["e", ("d", "f")], "block_type": "XOR", "end": None,
             "nested": [{"activities": ["d", "f"], "block_type": "PAR", "end": None, "nested": [], "start": None}],
             "start": None}
        ],
        
        "super": [{"activities": ["d", "e", "f"], "end": None, "start": None}],
    },
    "data_development/data/Log23_looselyStructured.json": {
        "blocks": [{"activities": ["a", "c"], "block_type": "PAR", "end": None, "nested": [], "start": None}],
        "super": [{"activities": ["a", "c"], "end": None, "start": None}],
    },
    "data_development/data/Log24_unstructured.json": {
        "blocks": [],
        "super": [],
    },
    "data_development/data/Log25_structured.json": {
        "blocks": [
            {"activities": [("b", "c", "d"), ("e", "f", "g"), ("h", "i", "j")], "block_type": "XOR", "end": "k", "nested": [], "start": "a"}
        ],
        "super": [{"activities": ["b", "c", "d", "e", "f", "g", "h", "i", "j"], "end": "k", "start": "a"}],
    },
    "data_development/data/Log26_structured.json": {
        "blocks": [{"activities": ["e", ("b", "c", "d")], "block_type": "XOR", "end": "f", "nested": [], "start": "a"}],
        "super": [{"activities": ["b", "c", "d", "e"], "end": "f", "start": "a"}],
    },
    "data_development/data/Log27_semiStructured.json": {
        "blocks": [{'activities': ['b', 'c'], 'block_type': 'PAR', 'end': 'd', 'nested': [], 'start': 'a'}],
        "super": [{'activities': ['b', 'c'], 'end': 'd', 'start': 'a'}]
    },
    "data_development/data/Log28_structured.json": {
        "blocks": [
            {"activities": ["b", "c"], "block_type": "PAR", "end": "d", "nested": [], "start": "a"},
            {"activities": ["e", ("f", "g", "h")], "block_type": "PAR", "end": "i",
             "nested": [{"activities": ["g", "h"], "block_type": "XOR", "end": "i", "nested": [], "start": None}],
             "start": "d"},
        ],
        
        "super": [{"activities": ["b", "c", "d", "e", "f", "g", "h"], "end": "i", "start": "a"}],
    }
}

def normalize_blocks(blocks):
    """
    Normalize blocks so order does not matter:
    - Represent nested tuples in 'activities' as canonical strings.
    - Sort by (block_type, activities, start, end).
    """
    def normalize_activity(act):
        if isinstance(act, tuple):
            # Convert tuples (possibly nested) into a stable string representation
            return "(" + ",".join(normalize_activity(a) for a in act) + ")"
        return str(act)

    def key(b):
        activities = [normalize_activity(a) for a in b.get("activities", [])]
        activities_sorted = sorted(activities)
        return (
            b.get("block_type"),
            activities_sorted,
            b.get("start") or "",
            b.get("end") or "",
        )

    return sorted(blocks, key=key)

def normalize_super(super_blocks):
    """
    Normalize super-blocks:
    - Sort activities inside each super-block.
    - Sort the list by (start, end, activities).
    """
    normalized = []
    for b in super_blocks:
        acts = sorted(list(b.get("activities", [])))
        normalized.append({
            "start": b.get("start"),
            "end": b.get("end"),
            "activities": acts,
        })

    def key(b):
        return (b.get("start"), b.get("end"), b.get("activities"))

    return sorted(normalized, key=key)


def verify_one(path, pp):
    """
    Load relationships, detect blocks and super-blocks, and compare
    with EXPECTED for the given path (if available).
    """
    print(f"\n=== {path} ===")

    relationships = load_relationships(path)
    blocks = detect_blocks(relationships)
    super_blocks = build_super_blocks(blocks, relationships)

    # If no expectation for this file, only show actual results
    if path not in EXPECTED:
        print("  ⚠️  No expected data – printing actual structures only.")
        print("  Blocks (normalized):")
        pp.pprint(normalize_blocks(blocks))
        print("  Super-blocks (normalized):")
        pp.pprint(normalize_super(super_blocks))
        return True  # not a failure

    exp = EXPECTED[path]
    ok = True

    # Compare blocks (order-invariant)
    norm_blk_exp = normalize_blocks(exp.get("blocks", []))
    norm_blk_act = normalize_blocks(blocks)
    if norm_blk_act != norm_blk_exp:
        print("  ❌  Blocks don’t match (order-invariant):")
        print("    expected:")
        pp.pprint(norm_blk_exp)
        print("    actual:")
        pp.pprint(norm_blk_act)
        ok = False

    # Compare super-blocks (order-invariant)
    norm_super_exp = normalize_super(exp.get("super", []))
    norm_super_act = normalize_super(super_blocks)
    if norm_super_act != norm_super_exp:
        print("  ❌  Super-blocks don’t match (order-invariant):")
        print("    expected:")
        pp.pprint(norm_super_exp)
        print("    actual:")
        pp.pprint(norm_super_act)
        ok = False

    if ok:
        print("  ✅  OK")


def main():
    for path in DEV_FILES:
        pp = pprint.PrettyPrinter(indent=2, width=120)
        verify_one(path, pp)

if __name__ == "__main__":
    main()
