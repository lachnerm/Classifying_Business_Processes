import argparse
import os
import pprint
from tabulate import tabulate

from utils import load_relationships
from block_detection import detect_blocks, build_super_blocks
from score_process import score_process
from constants import class_score_thresholds


def classify_process(data_dir, verbose):
    """
    Runs the process classification pipeline over all files in a directory.

    The pipeline loads pairwise activity relationships for each input file,
    detects control-flow blocks, aggregates them into super-blocks, and scores
    the process to derive a structuredness class.

    Args:
        data_dir (str): Directory containing the input files for classification.
            Filenames are expected to follow the pattern "<log>_<class>.json",
            e.g., "Order_Processing_structured.json". The function will process
            all regular files in this directory.
        verbose (bool): If True, print intermediate debug information and enable
            verbose mode in score_process.

    Returns:
        list: A list of rows summarizing results across all files.
    """
    # Collect files from directory (ignore subfolders)
    files = sorted(
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if os.path.isfile(os.path.join(data_dir, f))
    )

    summary_rows = []
    pp = pprint.PrettyPrinter()

    for path in files:
        # Parse filename: "<log>_<class>.json"
        filename = os.path.basename(path)
        stem, _ = os.path.splitext(filename)
        parts = stem.split("_")
        if len(parts) < 2:
            # Skip files that do not follow the expected naming convention
            print(f"Skipping '{filename}' (cannot parse '<log>_<class>')")
            continue
        log = "_".join(parts[:-1])
        class_real = parts[-1]

        # Load pairwise relationship data (temporal + existential)
        relationships = load_relationships(path)

        # Detect blocks and combine them into super-blocks
        blocks = detect_blocks(relationships)
        super_blocks = build_super_blocks(blocks, relationships)

        # Score the process to get the final score and details
        final_score, details = score_process(
            path, relationships, super_blocks, verbose=verbose
        )
        n_sbs_str, block_acts, outsiders, base_score, sb_sb_ref, out_sb_ref, out_out_ref, refinement = details

        # Map score to classification label using thresholds from constants.py
        if final_score < class_score_thresholds["unstructured"]:
            class_calc = "unstructured"
        elif final_score < class_score_thresholds["looselyStructured"]:
            class_calc = "looselyStructured"
        elif final_score < class_score_thresholds["semiStructured"]:
            class_calc = "semiStructured"
        else:
            class_calc = "structured"

        # Format insiders/outsiders for table output
        insider_str = ",".join(sorted(block_acts)) if block_acts else "-"
        outsider_str = ",".join(sorted(outsiders)) if outsiders else "-"

        # Append results to summary
        row = [
            log,
            n_sbs_str,
            insider_str,
            outsider_str,
            round(base_score, 3) if base_score is not None else None,
            round(sb_sb_ref, 3) if sb_sb_ref is not None else None,
            round(out_sb_ref, 3) if out_sb_ref is not None else None,
            round(out_out_ref, 3) if out_out_ref is not None else None,
            round(refinement, 3) if refinement is not None else None,
            round(final_score, 3) if final_score is not None else None,
            class_real,
            class_calc,
            "✅" if class_real == class_calc else "❌",
        ]
        summary_rows.append(row)

        # Optional verbose debug output
        if verbose:
            print(f"Log: {log}")
            print("  " + "-" * 80)
            print("  Blocks:")
            formatted = pp.pformat(blocks)
            print("\n".join("    " + line for line in formatted.splitlines()))
            print("  " + "-" * 80)
            print("  Super Blocks:")
            formatted = pp.pformat(super_blocks)
            print("\n".join("    " + line for line in formatted.splitlines()))
            print("=" * 80)

    return summary_rows


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run process structuredness classification over a directory of files."
    )
    parser.add_argument(
        "--dir",
        dest="data_dir",
        default="data_evaluation/data",
        help="Directory containing input files (default: data_evaluation/data).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug output and verbose mode in score_process.",
    )
    args = parser.parse_args()

    # Run classification
    summary_rows = classify_process(args.data_dir, verbose=args.verbose)

    # Print results table
    print(
        tabulate(
            summary_rows,
            headers=[
                "Log",
                "#SBs",
                "Insiders",
                "Outsiders",
                "Base-Score",
                "SB vs. SB",
                "Out vs. SB",
                "Out vs. Out",
                "Refinement",
                "Score",
                "Class Real",
                "Class Calculated",
                "Match",
            ],
            tablefmt="grid",
        )
    )


if __name__ == "__main__":
    main()
