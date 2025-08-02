import os
from score_processes import score_process
from tabulate import tabulate

from itertools import combinations
from utils import load_relationships, get_super_block_acts
from block_detection import detect_blocks, build_super_blocks
from tabulate import tabulate
import math
import os

if __name__ == "__main__":
    # Load data files
    directory = 'data/synthetic'
    files = sorted([os.path.join(directory, f) for f in os.listdir(directory)])

    # Score each file and aggregate results
    summary_rows = []
    for f in files:
        final_score, _ = score_process(f)
        log, class_real = f.split("/")[2].split(".")[0].split("_")
        
        if final_score < -0.4:
            class_calc = "unstructured"
        elif final_score < 0.25:
            class_calc = "looselyStructured"
        elif final_score < 0.75:
            class_calc = "semiStructured"
        else:
            class_calc = "structured"
        
        row = ([
            log,
            round(final_score, 2),
            class_real,
            class_calc,
            "✅" if class_real == class_calc else "❌"
        ])
        summary_rows.append(row)

    # print table of all results
    print(tabulate(
        summary_rows,
        headers=[
            "Log",
            "Score",
            "Class Real",
            "Class Calculated",
            "Match"
        ],
        tablefmt="grid"
    ))