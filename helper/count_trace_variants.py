import argparse
import os
import sys

from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.variants.log import get as variants_module


def analyze_xes_log_variants(xes_file_path):
    """
    Analyze and print trace variants of a single XES event log.

    The function loads the given XES log, extracts all unique variants
    (sequences of activities), counts their occurrences, sorts them
    alphabetically by the variant string, and prints a readable summary.

    Args:
        xes_file_path (str): Absolute or relative path to a .xes file.

    Returns:
        list: List of (variant, count) tuples sorted alphabetically by variant.
    """
    # Import the event log
    log = xes_importer.apply(xes_file_path)

    # Extract variants and count occurrences
    variants = variants_module.get_variants(log)
    variant_counts = {variant: len(traces) for variant, traces in variants.items()}

    # Sort variants alphabetically by the sequence of activities
    sorted_variants = sorted(variant_counts.items(), key=lambda item: item[0])

    # Pretty print summary
    print(f"File: {xes_file_path}")
    print(f"Number of different variants: {len(sorted_variants)}")
    print("=" * 50)
    for idx, (variant, count) in enumerate(sorted_variants, start=1):
        print(f"Variant {idx}: {variant}")
        print(f"  -> occurs in {count} cases.")
        print("-" * 50)

    return sorted_variants


def main():
    parser = argparse.ArgumentParser(
        description="Analyze variants of a single XES event log and print counts."
    )
    parser.add_argument(
        "xes_path",
        help="Path to a .xes file (absolute or relative)."
    )
    args = parser.parse_args()

    xes_path = args.xes_path

    # Basic validation before attempting to parse
    if not os.path.isfile(xes_path):
        print(f"Error: file not found: {xes_path}", file=sys.stderr)
        sys.exit(1)
    if not xes_path.lower().endswith(".xes"):
        print(f"Warning: file does not have .xes extension: {xes_path}", file=sys.stderr)

    try:
        analyze_xes_log_variants(xes_path)
    except Exception as e:
        # Catch-all to provide a helpful error message for common PM4Py issues
        print(f"Failed to analyze '{xes_path}': {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
