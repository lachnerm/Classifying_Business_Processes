from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.variants.log import get as variants_module

def analyze_xes_log_variants(xes_file_path):
    # Import the event log
    log = xes_importer.apply(xes_file_path)

    # Extract variants from the log
    variants = variants_module.get_variants(log)

    # Create a dictionary to store the count of each variant
    variant_counts = {}
    for variant, traces in variants.items():
        variant_counts[variant] = len(traces)

    # Sort variants alphabetically by the sequence of activities
    sorted_variants = sorted(variant_counts.items(), key=lambda item: item[0])

    print(f"Number of different variants: {len(sorted_variants)}")
    print("==================================================")
    for idx, (variant, count) in enumerate(sorted_variants, start=1):
        print(f"Variant {idx}: {variant}")
        print(f"  -> occurs in {count} cases.")
        print("--------------------------------------------------")


if __name__ == "__main__":
    FILES = [
        #"data_raw/Log01_structured.xes",
        #"data_raw/Log02_semiStructured.xes",
        #"data_raw/Log03_looselyStructured.xes",
        #"data_raw/Log04_structured.xes",
        #"data_raw/Log05_structured.xes",
        #"data_raw/Log06_semiStructured.xes",
        #"data_raw/Log07_semiStructured.xes",
        #"data_raw/Log08_looselyStructured.xes",
        #"data_raw/Log09_structured.xes",
        #"data_raw/Log10_semiStructured.xes",
        #"data_raw/Log11_looselyStructured.xes",
        #"data_raw/Log12_structured_non-blockstructuredness.xes",
        #"data_raw/Log13_semiStructured.xes",
        #"data_raw/Log14_looselySemiStructured.xes",
        #"data_raw/Log15_structured.xes",
        #"data_raw/Log16_looselyStructured.xes",
        #"data_raw/Log17_semiStructured.xes",
        #"data_raw/Log18_structured.xes",
        #"data_raw/Log19_structured.xes",
        #"data_raw/Log20_semiStructured.xes",
        #"data_raw/Log21_looselyStructured.xes",
        #"data_raw/Log22_looselyStructured.xes",
        #"data_raw/Log23_looselyStructured.xes",
        #"data_raw/Log24_looselyStructured.xes"
        #"data_raw/Augur.xes",
    ]
    for filename in FILES:
        analyze_xes_log_variants(filename)
