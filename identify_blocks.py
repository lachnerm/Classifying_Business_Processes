from utils import load_relationships
from block_detection import detect_blocks, build_super_blocks

if __name__ == "__main__":
    import pprint

    TEMP = [
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
        "data/synthetic/Log19_structured.json",
        "data/synthetic/Log20_semiStructured.json",
        "data/synthetic/Log21_looselyStructured.json",
        "data/synthetic/Log22_looselyStructured.json",
        "data/synthetic/Log23_looselyStructured.json",
        "data/synthetic/Log24_looselyStructured.json",
        "data/synthetic/Log25_structured.json",
        "data/synthetic/Log26_structured.json",
        "data/synthetic/Log27_semiStructured.json"
    ]
    FILES = [
        "data/real_data/augur.json",
    ]

    for f in FILES:
        relationships = load_relationships(f)
        blocks = detect_blocks(relationships)
        print("\n" + f)
        print("Blocks:")
        pprint.pprint(blocks, width=100)
        print("-" * 80)
        print("Super Blocks:")
        super_block = build_super_blocks(blocks, relationships)
        pprint.pprint(super_block, width=100)
        print("=" * 80)

