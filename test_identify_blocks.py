import sys
import pprint
from utils import load_relationships
from block_detection import detect_blocks, build_super_blocks

FILES = [
    "data/synthetic/Log01_structured.json",
    "data/synthetic/Log02_semiStructured.json",
    "data/synthetic/Log03_looselyStructured.json",
    "data/synthetic/Log04_structured.json",
    "data/synthetic/Log05_structured.json",
    "data/synthetic/Log06_semiStructured.json",
    "data/synthetic/Log07_semiStructured.json",
    "data/synthetic/Log08_looselyStructured.json",
    "data/synthetic/Log09_unstructured.json",
    "data/synthetic/Log10_semiStructured.json",
    "data/synthetic/Log11_looselyStructured.json",
    "data/synthetic/Log12_structured.json",
    "data/synthetic/Log13_semiStructured.json",
    "data/synthetic/Log14_looselySemiStructured.json",
    "data/synthetic/Log15_structured.json",
    "data/synthetic/Log16_looselyStructured.json",
    "data/synthetic/Log17_semiStructured.json",
    "data/synthetic/Log18_structured.json",
    "data/synthetic/Log20_semiStructured.json",
    "data/synthetic/Log21_looselyStructured.json",
    "data/synthetic/Log22_looselyStructured.json",
    "data/synthetic/Log23_looselyStructured.json",
    "data/synthetic/Log24_looselyStructured.json",
    #"data/synthetic/Log25_structured.json",
    "data/synthetic/Log26_structured.json",
    "data/synthetic/Log28_structured.json",
]

"""FILES = [
"data/synthetic/Log05_structured.json"
]"""

# Hard‑coded expected outputs 
EXPECTED = {
    "data/synthetic/Log01_structured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": ["c",("d","e")], "block_type": "XOR", "end": "f",
             "nested": [
                 {"activities": ["d","e"], "block_type": "PAR", "end": None, "nested": [], "start": None}
             ], "start": "b"},
        ],
        "edges": [],
        "super": [
            {"activities": ["b","c","d","e"], "end": "f", "start": "a"}
        ],
    },
    "data/synthetic/Log02_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": ["d","e"], "block_type": "XOR", "end": None, "nested": [], "start": "c"},
        ],
        "edges": [],
        "super": [
            {"activities": [], "end": "b", "start": "a"},
            {"activities": ["d","e"], "end": None, "start": "c"},
        ],
    },
    "data/synthetic/Log03_looselyStructured.json": {
        "blocks": [
            {   "activities": ["a", "e"],
                "block_type": "PAR",
                "end": None,
                "nested": [],
                "start": None
            },
            {   "activities": ["d", ("b", "c")],
                "block_type": "XOR",
                "end": None,
                "nested": [],
                "start": None
            }
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "e"], "end": None, "start": None},
            {"activities": ["b", "c", "d"], "end": None, "start": None}
        ],
    },
    "data/synthetic/Log04_structured.json": {
        "blocks": [
            {"activities": ["e","f"], "block_type": "XOR", "end": None, "nested": [], "start": "d"},
            {"activities": ["b","c"], "block_type": "PAR", "end": "d", "nested": [], "start": "a"},
        ],
        "edges": [],
        "super": [
            {"activities": ["b","c","d","e","f"], "end": None, "start": "a"},
        ],
    },
    "data/synthetic/Log05_structured.json": {
        "blocks": [
            {"activities": ["f", ("a", "c")], "block_type": "XOR", "end": None, "nested": [], "start": None},
            {"activities": ["b", "e"], "block_type": "XOR", "end": None, "nested": [], "start": None},
            {"activities": ["a", ("d", "f")], "block_type": "XOR", "end": None, "nested": [], "start": None}
        ],
        "edges": [(0, 1), (1, 0), (0, 2), (2, 0), (1, 0), (0, 1), (1, 2), (2, 1), (2, 0), (0, 2), (2, 1), (1, 2)],
        "super": [
            {"activities": ["a","b","c","d","e","f"], "end": None, "start": None},
        ],
    },
    "data/synthetic/Log06_semiStructured.json": {
        "blocks": [
            {"activities": ["b"], "block_type": "SEQUENCE", "end": "c", "nested": [], "start": "a"},
            {"activities": ["e","f"], "block_type": "PAR", "end": None, "nested": [], "start": "d"},
        ],
        "edges": [],
        "super": [
            {"activities": ["b"], "end": "c", "start": "a"},
            {"activities": ["e","f"], "end": None, "start": "d"},
        ],
    },
    "data/synthetic/Log07_semiStructured.json": {
        "blocks": [
            {"activities": [],       "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": [],       "block_type": "SEQUENCE", "end": "i", "nested": [], "start": "h"},
            {"activities": ["e","f"],"block_type": "XOR",      "end": "g", "nested": [], "start": "d"}
        ],
        "edges": [],
        "super": [
            {"activities": [],       "end": "b",   "start": "a"},
            {"activities": [],       "end": "i",   "start": "h"},
            {"activities": ["e","f"],"end": "g",   "start": "d"}
        ]
    },
    "data/synthetic/Log08_looselyStructured.json": {
        "blocks": [],
        "edges": [],
        "super": [],
    },
    "data/synthetic/Log09_unstructured.json": {
        "blocks": [
            {"activities": ["a", "b", "c"], "block_type": "PAR", "end": None, "nested": [], "start": None}
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "b", "c"], "end": None, "start": None}
        ],
    },
    "data/synthetic/Log10_semiStructured.json": {
        "blocks": [
            {"activities": [],       "block_type": "SEQUENCE", "end": "g", "nested": [], "start": "f"},
            {"activities": ["b"],"block_type": "SEQUENCE", "end": "c", "nested": [], "start": "a"},
        ],
        "edges": [],
        "super": [
            {"activities": [], "end": "g", "start": "f"},
            {"activities": ["b"],"end": "c", "start": "a"},
        ],
    },
    "data/synthetic/Log11_looselyStructured.json": {
        "blocks": [
            {"activities": ["d","e"],"block_type": "PAR", "end": None, "nested": [], "start": None},
        ],
        "edges": [],
        "super": [
            {"activities": ["d","e"],"end": None, "start": None},
        ],
    },
    "data/synthetic/Log12_structured.json": {
        "blocks": [
            {   "activities": [("b", "e", "f", "h"), ("c", "g"), ("d", "g")],
                "block_type": "XOR",
                "end": None,
                "nested": [   { "activities": ["f", ("e", "h")],
                                "block_type": "PAR",
                                "end": None,
                                "nested": [],
                                "start": None}],
                "start": "a"},
            
        ],
        "edges": [],
        "super": [
            {"activities": ["b", "c", "d", "e", "f", "g", "h"], "end": None, "start": "a"}
        ]
    },
    "data/synthetic/Log13_semiStructured.json": {
        "blocks": [
            {   "activities": ["g", "h"],
                "block_type": "PAR",
                "end": None,
                "nested": [],
                "start": None},
            {   "activities": [("c", "i", "j"), ("d", "e", "f")],
                "block_type": "XOR",
                "end": None,
                "nested": [],
                "start": None}
        ],
        "edges": [],
        "super": [   
            {"activities": ["c", "d", "e", "f", "i", "j"], "end": None, "start": None},
            {"activities": ["g", "h"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log14_looselySemiStructured.json": {
        "blocks": [
            {   "activities": ["becomeHoly", "curse"],
                "block_type": "XOR",
                "end": None,
                "nested": [],
                "start": None
            }
        ],
        "edges": [],
        "super": [
            {"activities": ["becomeHoly", "curse"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log15_structured.json": {
        "blocks": [   
            {
                "activities": [],
                "block_type": "SEQUENCE",
                "end": "g",
                "nested": [],
                "start": "f"
            },
            {   
                "activities": ["e", ("b", "c", "d")],
                "block_type": "XOR",
                "end": "f",
                "nested": [{   "activities": ["b", "c", "d"],
                          "block_type": "PAR",
                          "end": None,
                          "nested": [],
                          "start": None}],
                "start": "a"},
            {   "activities": ["h"],
                "block_type": "OPTIONAL",
                "end": "i",
                "nested": [],
                "start": "g"
            }
        ],
        "edges": [(2,1)],
        "super": [
            {"activities": ["b","c","d","e","f","g","h"], "end": "i", "start": "a"}
        ]
    },
    "data/synthetic/Log16_looselyStructured.json": {
        "blocks": [
            {"activities": ["a", "b"], "block_type": "PAR", "end": None, "nested": [], "start": None}
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "b"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log17_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "b", "nested": [], "start": "a"},
            {"activities": ["c", "d"], "block_type": "PAR", "end": "e", "nested": [], "start": "b"}
        ],
        "edges": [],
        "super": [
            {"activities": ["b", "c", "d"], "end": "e", "start": "a"}
        ]
    },
    "data/synthetic/Log18_structured.json": {
        "blocks": [
            {"activities": [("a", "b"), ("c", "d")], "block_type": "PAR", "end": None, "nested": [], "start": None}
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "b", "c", "d"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log19_structured.json": {
        "blocks": [
            {"activities": ["a", "b"], "block_type": "XOR", "end": None, "nested": [], "start": None},
            {"activities": ["d", "e"], "block_type": "PAR", "end": None, "nested": [], "start": None}
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "b"], "end": None, "start": None},
            {"activities": ["d", "e"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log20_semiStructured.json": {
        "blocks": [
            {"activities": [], "block_type": "SEQUENCE", "end": "e", "nested": [], "start": "d"},
            {"activities": ["b", "c"], "block_type": "XOR", "end": None, "nested": [], "start": "a"}
        ],
        "edges": [],
        "super": [
            {"activities": [], "end": "e", "start": "d"},
            {"activities": ["b", "c"], "end": None, "start": "a"}
        ]
    },
    "data/synthetic/Log21_looselyStructured.json": {
        "blocks": [
            {"activities": ["b", "c"], "block_type": "PAR", "end": None, "nested": [], "start": None}
        ],
        "edges": [],
        "super": [
            {"activities": ["b", "c"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log22_looselyStructured.json": {
        "blocks": [
            {"activities": ["e", ("d", "f")], "block_type": "XOR", "end": None, 
             "nested": [
                {"activities": ["d", "f"],
                    "block_type": "PAR",
                    "end": None,
                    "nested": [],
                    "start": None}],
            "start": None}
        ], 
        "edges": [],
        "super": [
            {"activities": ["d", "e", "f"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log23_looselyStructured.json": {
        "blocks": [
            {"activities": ["e", ("d", "f")], "block_type": "XOR", "end": None, 
             "nested": [
                {"activities": ["d", "f"],
                    "block_type": "PAR",
                    "end": None,
                    "nested": [],
                    "start": None}],
            "start": None}
        ], 
        "edges": [],
        "super": [
            {"activities": ["d", "e", "f"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log24_looselyStructured.json": {
        "blocks": [
            {"activities": ["a", "c"], "block_type": "PAR", "end": None, "nested": [], "start": None}
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "c"], "end": None, "start": None}
        ]
    },
    "data/synthetic/Log25_structured.json": {
        "blocks": [
            {   "activities": [("b", "c", "d"), ("e", "f", "g"), ("h", "i", "j")],
                "block_type": "XOR",
                "end": "k",
                "nested": [],
                "start": "a"
            }
        ],
        "edges": [],
        "super": [
            {"activities": ["b", "c", "d", "e", "f", "g", "h", "i", "j"], "end": "k", "start": "a"}
        ]
    },
    "data/synthetic/Log26_structured.json": {
        "blocks": [
            {   "activities": ["e", ("b", "c", "d")],
                "block_type": "XOR",
                "end": "f",
                "nested": [],
                "start": "a"
            }
        ],
        "edges": [],
        "super": [
            {"activities": ["b", "c", "d", "e"], "end": "f", "start": "a"}
        ]
    },
    "data/synthetic/Log28_structured.json": {
        "blocks": [
            {"activities": ["b", "c"], "block_type": "PAR", "end": "d", "nested": [], "start": "a"},
            {"activities": ["e", ("f", "g", "h")],
            "block_type": "PAR",
            "end": "i",
            "nested": [{"activities": ["g", "h"],
                        "block_type": "XOR",
                        "end": None,
                        "nested": [],
                        "start": None}],
            "start": "d"}
        ],
        "edges": [],
        "super": [
            {"activities": ["b", "c", "d", "e", "f", "g", "h"], "end": "i", "start": "a"}
        ]
    },
    "data/synthetic/Log29_unstructured.json": {
        "blocks": [],
        "edges": [],
        "super": []
    },
    "data/synthetic/Log30_semiStructured.json": {
        "blocks": [
            {   "activities": [("a", "b"), ("c", "d")],
                "block_type": "XOR",
                "end": None,
                "nested": [],
                "start": None
            }
        ],
        "edges": [],
        "super": [
            {"activities": ["a", "b", "c", "d"], "end": None, "start": None}
        ]
    },
}

def normalize_blocks(blocks):
    """
    Sort blocks by (block_type, activities tuple, start, end) so that order no longer matters.
    Nested tuples in activities are converted to strings for consistent comparison.
    """
    def normalize_activity(act):
        if isinstance(act, tuple):
            return f"({",".join(normalize_activity(a) for a in act)})"
        return str(act)

    def key(b):
        return (
            b["block_type"],
            sorted(tuple(normalize_activity(a) for a in b["activities"])),
            b.get("start") or "",
            b.get("end") or ""
        )

    return sorted(blocks, key=key)


def normalize_edges(edges):
    """Sort edges (i,j) so order no longer matters."""
    return sorted(edges)

def normalize_super(super_blocks):
    for b in super_blocks:
        b["activities"] = sorted(b["activities"])
    def key(b):
        return (b["start"], b["end"], b["activities"])
    return sorted(super_blocks, key=key)


def main():
    pp = pprint.PrettyPrinter(indent=4)
    failures = 0

    for path in FILES:
        print(f"\n=== {path} ===")
        relationships = load_relationships(path)
        blocks = detect_blocks(relationships)
        super_blocks = build_super_blocks(blocks, relationships)


        if path not in EXPECTED:
            print("  ⚠️  No expected data – skipping comparison.")
            continue

        exp = EXPECTED[path]
        ok = True

        # normalize both expected and actual
        norm_blk_exp = normalize_blocks(exp["blocks"])
        norm_blk_act = normalize_blocks(blocks)
        if norm_blk_act != norm_blk_exp:
            print("  ❌  Blocks don’t match (order‐invariant):")
            print("    expected:")
            pp.pprint(norm_blk_exp)
            print("    actual:")
            pp.pprint(norm_blk_act)
            ok = False

        norm_super_exp = normalize_super(exp["super"])
        norm_super_act = normalize_super(super_blocks)
        if norm_super_act != norm_super_exp:
            print("  ❌  Super‑blocks don’t match (order‐invariant):")
            print("    expected:")
            pp.pprint(norm_super_exp)
            print("    actual:")
            pp.pprint(norm_super_act)
            ok = False

        if ok:
            print("  ✅  OK")
        else:
            failures += 1

    print(f"\n{failures} file(s) failed." if failures else "\nAll tests passed!")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()