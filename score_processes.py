
from itertools import combinations
from utils import load_relationships, get_super_block_acts
from block_detection import detect_blocks, build_super_blocks
from tabulate import tabulate
import math
import os

REFINEMENT_SCORES_SB_TO_SB = {
    # Don't occur
    #(">d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #("<d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #("-",  "∧"):    -0.60,  # NAND (parallel)
    #("-",  "v"):    -0.60,  # OR relationship
    #("<d", "=>"):   +0.30,  # directly leads‑to
    #(">d", "=>"):   +0.30,  # directly leads‑to
    #("<d", "<="):   +0.30,  # directly precedes
    #(">d", "<="):   +0.30,  # directly precedes
    #("-",  "</=>"): +0.30,  # non‑co‑occurrence (XOR)
    #(">",  "<="):   +0.50,  # precedes
    #("<",  "<="):   +0.50,  # precedes
    #("<d", "-"):    +0.30,  # direct before
    #(">d", "-"):    +0.30,  # direct after

    # Can occur if there is a fragment that can (but does not have to) occur between two blocks that are ordered
    # For example log 6, g can occur between both blocks
    # Also occurs in log 7, 10, 20
    ("<",  "<=>"):  +0.15,  # ordered co‑occurrence
    (">",  "<=>"):  +0.15,  # ordered co‑occurrence

    # Similar to ordered co-occurence, but only one-way existential implication
    # For example log 20, d comes after b/c (XOR without merge) but since neither b nor c have to exist (only one), no co-occurence
    # No further occurences
    # Same value as ordered co-occurence as this is only artifact of missing merge
    ("<",  "=>"):   +0.15,  # leads‑to
    (">",  "<="):   +0.15,  # precedes

    # Can occur if two blocks are existentially independent, neither has to occur, but if they do, there is a temporal ordering
    # For example log 13 XOR (b(c,d)) and PAR (g,h) -> here comes from c+d being in XOR and therefore not having to occur, special case
    # No further occurences
    ("<",  "-"):    +0.10,   # before
    (">",  "-"):    +0.10,   # after

    # Can occur if there are blocks that both have to occur but have no temporal ordering
    # For example log 2 sequence (a,b) and XOR (c,(d,e)) -> (b,c) since both acts have to occur
    # Also occurs in log 7
    ("-",  "<=>"):  -0.05,   # co‑occurrence (Parallel)

    # Can occur if two blocks exist but they have no temporal ordering - one block is XOR split without merge, other sequence
    # -> open acts in XOR don't have to occur, so one way implication
    # For example log 2 sequence (a,b) and XOR (c,(d,e)) with d XOR e -> (d,a)
    # No further occurences
    # NOTE: Same value as co-occurence as this is only artifact of missing merge
    ("-",  "=>"):   -0.05,   # implication (right)
    
    # Can occur for complicated nesting, e.g. log 19
    ("-",  "<="):   -0.05,   # implication (left)

    # Can occur if two blocks are fully independent - no temporal ordering, neither has to occur
    # For example log 3 PAR (a,e) and XOR (d,(b,c))
    # Also occurs in log 13
    ("-",  "-"):    -0.25,   # fully independent
}

REFINEMENT_SCORES_OUT_TO_SB = {
    # Note: Weights are smaller here than others as outsiders are already penalized via base score, don't penalize to strong here

    # Don't occur
    #("<d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #(">d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #("<d", "=>"):   +0.80,  # directly leads‑to
    #(">d", "=>"):   +0.80,  # directly leads‑to
    #("-",  "</=>"): +0.70,  # non‑co‑occurrence (XOR)
    #("<d", "-"):    +0.60,  # direct before
    #("-",  "∧"):    -0.30,  # NAND (parallel)
    #("-",  "v"):    -0.30,  # OR relationship
    #("<",  "-"):    +0.05,  # before
    #("<",  "<=>"):  +0.50,  # ordered co‑occurrence
    #("<d", "<="):   +0.25,  # directly precedes
    #("<d", "-"):    +0.10,  # direct before
    #("-",  "</=>"): +0.20,  # non‑co‑occurrence (XOR)
    #(">d", "<="):   +0.25,  # directly precedes

    # All of these can occur if block and outsider have to occur with temporal ordering, but other outsiders or fragments can occur in between
    # For example log 20, XOR (a,(b,c)) and g both occur with a being first, but many other activities can occur in between
    # No further occurences
    ("<",  "<=>"):  +0.25,  # ordered co‑occurrence
    (">",  "<=>"):  +0.25,  # ordered co‑occurrence

    # Can occur if block and outsider have to occur without temporal ordering
    # For example log 20, sequence (d,e) and g both occur without any order
    # No further occurences
    ("-",  "<=>"):  +0.20,  # co‑occurrence (Parallel)

    # Can occur with "response" relationship from outsider to block, i.e. outsider comes before block but doesn't have to
    # For example log 11, f has response relationship to PAR (d,e)
    # Also occurs in log 21
    ("<",  "=>"):   +0.15,  # leads‑to

    # Can occur if outsider precedes a block, it comes before 
    # For example log 3, f precedes c
    # Also occurs in log 13, 21, 22, 23
    ("<",  "<="):   +0.15,  # precedes

    # Can occur if outsider comes after block but doesn't have to occur
    # For example log 7, c can come after sequence (a,b) but doesn't have to
    # Also occurs in log 10, 12, 17, 18, 20
    (">",  "=>"):   +0.15,  # leads‑to

    # Can occur if outsider is response to a block, it comes after
    # For example log 14, pray is response to curse
    # Also occurs in log 12, 19, 20
    (">",  "<="):   +0.15,  # precedes

    # Can occur in complex block nesting that is not captured correctly, e.g. if one branch ends in another activity directly, but can also skip this activity and it can be reached else
    # For example log 12 for (i,g), i can directly follow g, but process can end after g as well, and i can be reached by separate branch
    (">d", "-"):    +0.10,  # direct after

    # Can occur if outsider and block both don't have to exists, but if they do, they have a temporal ordering
    # For example log 20, XOR (a,(b,c)) and f -> here for (f,b) and (f,c), but is due to no merge for XOR, special case
    # Also occurs in log 12
    (">",  "-"):    +0.05,  # after


    # Can occur if outsider and block have no temporal ordering, but one-way existential
    # For example log 3, XOR (d,(b,c)) and f for (f,b)
    # Also occurs in log 14, 19, 30
    ("-",  "<="):   -0.10,  # implication (left)

    # Can occur if block has to exist but outsider is optional without temporal ordering
    # For example log 2, XOR (c,(d,e)) and f for (f,c)
    # Also occurs in log 6, 7, 10, 17, 18, 20, 21
    ("-",  "=>"):   -0.10,  # implication (right)
    
    # Can occur for multiple reasons, easiest one: no temporal or existential relationship, straightforward
    # Can also occur due to XOR (e.g. log 2) without merge due to missing existential link
    # Occurs in log 2, 3, 7, 11, 13, 14, 16, 21, 22, 23, 24
    ("-",  "-"):    -0.20,  # fully independent
}

REFINEMENT_SCORES_OUT_TO_OUT = {
    # Don't occur
    #("<d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #(">d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #("<d", "=>"):   +0.80,  # directly leads‑to
    #("<d", "-"):    +0.60,  # direct before
    #(">d", "-"):    +0.60,  # direct after
    #("-",  "∧"):    -0.30,  # NAND (parallel)
    #("-",  "v"):    -0.30,  # OR relationship
    #(">",  "<=>"):  +1.00,  # ordered co‑occurrence
    #("<d",  "-"):    +0.40,  # direct before
    #(">",  "=>"):   +0.50,  # leads‑to

    # Can occur if complex block nesting doesn't capture all block activities e.g. log 19
    # Can occur for succession relationship, e.g log 8
    # Can occur if there is a sequence but other outsiders can occur in between, therefore not capturing sequence, e.g. log 13
    # Also occurs in log 17, 19, 20, 22, 23
    ("<",  "<=>"):  +0.25,  # ordered co‑occurrence
    # NEW after not sorting
    (">",  "<=>"):  +0.25,  # ordered co‑occurrence

    # For example log 8, (a,b)
    # No further occurences
    ("<d", "<="):   +0.20,  # directly precedes
    ("<d", "=>"):   +0.20,  # directly leads‑to
    (">d", "<="):   +0.20,  # directly precedes
    (">d", "=>"):   +0.20,  # directly leads‑to

    # Can occur if XOR relationship exists but boundary conditions for XOR block are not met, e.g. log 8
    # No further occurences
    ("-",  "</=>"): +0.10,  # non‑co‑occurrence

    # Can occur if complex block nesting doesn't capture all block activities e.g. log 19
    # Can occur if PAR relationships exists but boundary conditions for PAR blocks are not met, e.g. log 20
    # No further occurences
    ("-",  "<=>"):  +0.10,  # co‑occurrence (Parallel)

    # For example log 16, (c,d)
    # Log 11
    ("<",  "=>"):   +0.10,  # leads‑to
    # Log 8 (e,a)
    (">",  "=>"):   +0.10,  # leads‑to

    # Occurs in log 8, 13, 21
    ("<",  "<="):   +0.10,  # precedes

    # For example log 11, (b,c)
    # No further occurences
    (">",  "<="):   +0.10,  # precedes

    # For example log 8, (b,g)
    # Also occurs in log 18
    # No further occurences
    ("<",  "-"):    -0.05,  # before
    (">",  "-"):    -0.05,  # after

    # Occurs in log 8, 13, 20
    ("-",  "<="):   -0.15,  # implication (left)

    # Occurs in log 8, 11, 14, 20
    ("-",  "=>"):   -0.15,  # implication (right)
    
    # Occurs often
    ("-",  "-"):    -0.25,  # fully independent
}


def compute_base_score(super_blocks, all_acts, entropy_penalty=0.4, outsider_penalty_exponent=1.5):
    """
    Compute a structuredness score for a set of super-blocks in a process.

    The score captures how well the overall process is covered by the super-blocks,
    and how fragmented this coverage is. It combines:
    - Total coverage (how many activities are included in any super-block),
    - Normalized entropy (how evenly that coverage is distributed across blocks),
    - A penalty for unstructured "outsider" activities not covered by any block.

    A high score indicates a well-structured process with few, large, coherent fragments.
    A low score suggests high fragmentation or low coverage.

    Args:
        super_blocks (list of dict): Each dictionary describes a super-block and must contain:
            - "activities": list of inner activities
            - "start": start activity (or None)
            - "end": end activity (or None)
        all_acts (list of str): List of all activity names in the full process model.
        outsider_penalty_exponent (float): Exponent to penalize uncovered activities.
            Higher values increase the penalty for uncovered activities.

    Returns:
        base_score (float): Structuredness score in [0, 1], higher = more structured.
        outsider_acts (list of str): Activities not covered by any super-block.
        reason (str): Explanation string summarizing number of super-blocks.
    """

    # Convert activity list to set for faster lookups
    all_acts_set = set(all_acts)

    # Collect all activities that are covered by any super-block (including start/end)
    covered_acts = set()
    for sb in super_blocks:
        covered_acts.update(sb["activities"])
        if sb["start"]:
            covered_acts.update(sb["start"])
        if sb["end"]:
            covered_acts.update(sb["end"])

    # Identify uncovered activities
    outsider_acts = all_acts_set - covered_acts
    total_activity_count = len(all_acts_set)

    # Compute coverage fraction for each super-block
    coverage_fractions = []
    for sb in super_blocks:
        covered_in_block = len(sb["activities"])
        if sb["start"]:
            covered_in_block += 1
        if sb["end"]:
            covered_in_block += 1

        coverage_fraction = covered_in_block / total_activity_count if total_activity_count else 0.0
        coverage_fractions.append(coverage_fraction)

    # Compute total process coverage
    total_coverage = sum(coverage_fractions)

    # Compute normalized entropy over the coverage fractions to measure fragmentation
    num_blocks = len(super_blocks)
    entropy = 0
    if num_blocks > 1:
        for frac in coverage_fractions:
            p_i = frac / total_coverage
            entropy -= p_i * math.log(p_i)
        entropy = entropy / math.log(num_blocks)

    # Derive a structure factor that rewards low fragmentation
    structure_factor = 1.0 - entropy_penalty * entropy

    # Combine structure and coverage with penalty for uncovered activities
    base_score = structure_factor * (total_coverage ** outsider_penalty_exponent)

    # Prepare summary explanation based on number of super-blocks
    if num_blocks == 0:
        reason = "0 SB"
    elif num_blocks == 1:
        reason = "1 SB"
    else:
        reason = f"{num_blocks} SB"

    return base_score, outsider_acts, reason


def refine_sb_to_sb(relations, super_blocks, verbose):
    """
    Compute a refinement score based on the relationships between super-blocks.

    Each super-block may define a start and end activity. If these are not defined,
    its internal activities are used instead. The idea is to evaluate how well the
    process structure supports direct transitions from one super-block to the next.

    For each ordered pair of super-blocks (SB_i → SB_j), we compare every end activity
    of SB_i to every start activity of SB_j. For each such pair of activities, we
    extract the temporal and existential relation and use a pre-defined scoring
    scheme (REFINEMENT_SCORES_SB_TO_SB) to assign a numeric score.

    Parameters
    ----------
    all_acts : set of str
        All activity names in the process.
    relations : dict of dict
        Pairwise relationships between activities, with format relations[a][b] = "<temporal>,<existential>".
    super_blocks : list of dict
        List of super-blocks, each defined by:
        - "activities": list of inner activities
        - "start": list of start anchors (can be empty)
        - "end": list of end anchors (can be empty)
    verbose : bool
        If True, print detailed intermediate output.

    Returns
    -------
    refinement : float
        Refinement score, higher values indicate stronger connectivity between super-blocks.
    """

    if verbose:
        print("-" * 80 + "\n")
        print("Refinement SB vs. SB:")

    # Store all per-pair relation scores
    scores = []  
    # Keep track of all activities that are part of any super-block
    all_sb_acts = set()  

    # Compare every pair of super-blocks (excluding self-pairs)
    for idx1, sb1 in enumerate(super_blocks):

        # Add all activities (incl. start/end if present) from current SB to the set
        all_sb_acts.update(set(get_super_block_acts(sb1)))

        for idx2, sb2 in enumerate(super_blocks):
            if idx1 == idx2:
                continue  # skip self-comparisons

            # Use defined end activities if available, else fall back to internal activities
            end_acts = sb1["end"] if sb1["end"] else sb1["activities"]
            # Use defined start activities if available, else fall back to internal activities
            start_acts = sb2["start"] if sb2["start"] else sb2["activities"]

            if verbose:
                print(f"\nSB{idx1+1}→SB{idx2+1}: end {end_acts} → start {start_acts}")

            # For each combination of end→start activities, look up relation score
            for end in end_acts:
                for start in start_acts:
                    temp, exist = relations[end][start].split(",")
                    score = REFINEMENT_SCORES_SB_TO_SB.get((temp, exist))
                    if not score:
                        raise KeyError(f"Unknown relation ({temp},{exist}) for ({end},{start})")
                    scores.append(score)
                    if verbose:
                        print(f"    ({end}→{start}) = ({temp},{exist}) → {score:+.2f}")

    # Average over all comparisons
    refinement = sum(scores) / len(scores) 

    if verbose:
        print(f"\nRefinement SB vs. SB: {refinement:+.2f}")

    return refinement


def refine_out_to_sb(outsiders, relations, super_blocks, verbose):
    """
    Compute a refinement score based on the relationships between super-blocks and outsiders.

    For each outsider activity, the function compares it to every activity within 
    each super-block (including start and end activities, if defined).
    Each pairwise relationship is mapped to a numeric score based on a predefined 
    refinement scoring table.

    The average is computed across all outsider-to-super-block activity pairs. 

    Parameters
    ----------
    outsiders : list of str
        List of activities not covered by any super-block.
    relations : dict of dict
        Pairwise relationships between activities, with format relations[a][b] = "<temporal>,<existential>".
    super_blocks : list of dict
        List of super-blocks, each defined by:
        - "activities": list of inner activities
        - "start": list of start anchors (can be empty)
        - "end": list of end anchors (can be empty)
    verbose : bool
        If True, print detailed intermediate output.

    Returns
    -------
    refinement : float
        The refinement score between outsiders and super-blocks.
    """

    if verbose:
        print("-" * 80 + "\n")
        print("Refinement Out vs. SB:")

    # Collect all pairwise scores between outsider activities and SB activities
    scores = []

    # Iterate over each outsider activity
    for outsider in outsiders:
        if verbose:
            print(f"Out → {outsider}")

        # Compare this outsider to every super-block
        for idx, sb in enumerate(super_blocks):
            # Get all activities associated with this SB (internal + optional start/end)
            acts = get_super_block_acts(sb)

            if verbose:
                print(f"  SB{idx+1} → {acts}")

            # For each activity in the super-block, compare it to the outsider
            for act in acts:
                # Extract the pairwise relationship (temporal and existential)
                temp, exist = relations[outsider][act].split(",")

                # Map the relationship to a numeric refinement score
                score = REFINEMENT_SCORES_OUT_TO_SB.get((temp, exist))
                if not score:
                    raise KeyError(f"Unknown relation ({temp},{exist}) for ({outsider},{act})")

                scores.append(score)

                if verbose:
                    print(f"    ({outsider}→{act}) = ({temp},{exist}) → {score:+.2f}")

    # Compute the average refinement score across all outsider–SB activity pairs
    refinement = sum(scores) / len(scores) if scores else 0

    if verbose:
        print(f"Refinement Out {outsider} vs. SB: {refinement:+.2f}")

    return refinement


def refine_out_to_out(outsiders, relations, verbose):
    """
    Compute a refinement score based on the relationships between outsider activities.

    This score captures how strongly activities that are not part of any super-block
    (outsiders) are connected to each other. For every unordered pair of outsider
    activities, the function retrieves their pairwise relationship (temporal and 
    existential), and maps it to a numerical score using a predefined table.

    Parameters
    ----------
    all_acts : set of str
        All activity names in the process.
    outsiders : list of str
        Activities that are not covered by any super-block.
    relations : dict of dict
        Pairwise relationships between activities, with format relations[a][b] = "<temporal>,<existential>".
    verbose : bool
        If True, print detailed intermediate output.

    Returns
    -------
    refinement : float
        Refinement score indicating structural connectivity among outsiders.
    """

    if verbose:
        print("--------------------------------------------------------------------------------\n")
        print("Refinement Out vs. Out:")

    # Store all pairwise refinement scores between outsiders
    scores = []

    # Iterate over all unique unordered pairs of outsiders (no self-pairs)
    for out1, out2 in combinations(outsiders, 2):
        # Extract temporal and existential relationship
        temp, exist = relations[out1][out2].split(",")
        # Map to refinement score using predefined dictionary
        score = REFINEMENT_SCORES_OUT_TO_OUT.get((temp, exist))
        if not score:
            raise KeyError(f"Unknown relation ({temp},{exist}) for ({out1},{out2})")
        scores.append(score)

        if verbose:
            print(f"    ({out1}→{out2}) = ({temp},{exist}) → {score:+.2f}")

    # Compute average score over all comparisons
    refinement = sum(scores) / len(scores)

    if verbose:
        print(f"\nRefinement Out vs. Out: {refinement:+.2f}")

    return refinement


def compute_refinement_weights(
    all_acts,
    super_blocks,
    pair_sum=2.0,
    imbalance_gamma=1.0,
    bridge_base=2.0,
    bridge_strength=1.0,
    bridge_gamma=1.0
):
    """
    Computes adaptive weights for the three refinement types:
    - SB to SB (between super-blocks)
    - Out to SB (between outsiders and super-blocks)
    - Out to Out (between outsiders)

    These weights adapt dynamically to the structural distribution of the process:
    - If most activities are in super-blocks, the SB to SB weight increases.
    - If most are outsiders, the Out to Out weight increases.
    - Out to SB is highest in balanced settings and shrinks with increasing imbalance.

    Parameters:
        all_acts (iterable): Set or list of all activities in the process.
        super_blocks (iterable): Each block is a dict with at least the key "activities".
                                 Optional keys: "start", "end".
        pair_sum (float): Target sum of SB to SB and Out to Out weights (default: 2.0).
        imbalance_gamma (float): Controls the steepness of the SB vs. Out tradeoff (>= 0).
                                 Higher values increase sensitivity to imbalance.
        bridge_base (float): Base weight of Out to SB at perfect balance (default: 2.0).
        bridge_strength (float): In [0, 1]. Defines how much the bridge shrinks with imbalance.
                                 A value of 1 means the bridge can shrink to 0.
        bridge_gamma (float): Controls the sensitivity of the bridge to imbalance (>= 0).

    Returns:
        tuple: (weight_sb_sb, weight_out_sb, weight_out_out), all floats.
    """

    # Collect all activities covered by super-blocks (including optional start/end)
    all_sb_acts = set()
    for block in super_blocks:
        all_sb_acts.update(block["activities"])
        if block["start"]:
            all_sb_acts.add(block["start"])
        if block["end"]:
            all_sb_acts.add(block["end"])

    # Count how many activities are covered by super-blocks and by outsiders
    n_total_acts = len(all_acts)
    n_sb_acts = len(all_sb_acts)
    n_outs = n_total_acts - n_sb_acts

    # Edge case: no super-blocks
    if n_sb_acts == 0:
        return 0.0, 0.0, pair_sum

    # Edge case: no outsiders
    if n_outs == 0:
        return pair_sum, 0.0, 0.0

    # Edge case: 1 SB and 1 outsider
    if n_outs == 1 and len(super_blocks) == 1:
        return 0.0, bridge_base, 0.0

    # Compute imbalance between SB and outsider activities: value in [-1, 1]
    imbalance = (n_sb_acts - n_outs) / float(n_total_acts)

    # Transform imbalance based on sensitivity (gamma)
    weighted_imbalance = imbalance ** imbalance_gamma

    # SB to SB and Out to Out share the pair_sum, depending on imbalance
    weight_sb_sb = pair_sum * ((weighted_imbalance + 1) / 2)
    weight_out_out = pair_sum - weight_sb_sb 

    # Out to SB (bridge) is maximal when balanced, shrinks symmetrically with imbalance
    bridge_shrinkage = bridge_strength * (abs(imbalance) ** bridge_gamma)
    weight_out_sb = bridge_base * (1.0 - bridge_shrinkage)

    return weight_sb_sb, weight_out_sb, weight_out_out

def score_process(path, verbose=False):
    """
    Computes the overall structuredness score for a given process log.

    This includes the following steps:
    - Load pairwise activity relationships from the given JSON file.
    - Detect control-flow blocks based on patterns (e.g., XOR, PAR, optional).
    - Merge blocks into super-blocks that form larger coherent process fragments.
    - Compute a base structuredness score based on coverage and entropy.
    - Compute refinement terms based on relationships between super-blocks and outsiders.
    - Combine all components into a final structuredness score.

    Parameters
    ----------
    path : str
        Path to the JSON file containing pairwise activity relationships.
    verbose : bool, default=False
        If True, print detailed progress and score information to stdout.

    Returns
    -------
    final_score : float
        The overall structuredness score for the process.
    row : list
        List of elements summarizing the process and all score components, useful for CSV output:
        [
            process name,
            reason string (e.g., "3 SB"),
            comma-separated insider activities,
            comma-separated outsider activities,
            base score (rounded),
            SB-to-SB refinement score (rounded or None),
            SB-to-outsider refinement score (rounded or None),
            outsider-to-outsider refinement score (rounded or None),
            total refinement (rounded),
            final score (rounded)
        ]
    """

    if verbose:
        print("\n" + "=" * 80)
        print(f"ANALYSIS FOR {path}\n")

    # Load pairwise relationship data (temporal + existential) between activities
    relationships = load_relationships(path)

    # Identify all control-flow blocks based on the relationships
    blocks = detect_blocks(relationships)

    # Merge connected blocks into higher-level super-blocks
    super_blocks = build_super_blocks(blocks, relationships)

    # Get the full list of activities from the relationship data
    all_acts = set(relationships.keys())


    # Compute the base structuredness score based on coverage and fragmentation
    base_score, outsiders, reason = compute_base_score(super_blocks, all_acts)

    # Compute weights for each of the refinements
    weight_sb_sb, weight_out_sb, weight_out_out = compute_refinement_weights(all_acts, super_blocks)

    all_refs = []

    # Compute refinement score between all super-blocks
    # Only if there are at least two super-blocks
    if len(super_blocks) > 1:
        sb_sb_ref = weight_sb_sb * refine_sb_to_sb(relationships, super_blocks, verbose)
        all_refs.append(sb_sb_ref)
        if verbose:
            print(f"Weighted Refinement SB vs. SB: {sb_sb_ref:+.2f} (Factor: {weight_sb_sb:+.2f})")
    else:
        sb_sb_ref = None

    # Compute refinement score between outsider activities and super-blocks 
    # Only if there is at least one of each to compare
    if len(super_blocks) >= 1 and len(outsiders) >= 1:
        out_sb_ref = weight_out_sb * refine_out_to_sb(outsiders, relationships, super_blocks, verbose)
        all_refs.append(out_sb_ref)
        if verbose:
            print(f"Weighted Refinement Out vs. SB: {out_sb_ref:+.2f} (Factor: {weight_out_sb:+.2f})")
    else:
        out_sb_ref = None

    # Compute refinement score between outsider activities
    # Only if there are at least two outsiders to compare
    if len(outsiders) > 1:
        out_out_ref = weight_out_out * refine_out_to_out(outsiders, relationships, verbose)
        all_refs.append(out_out_ref)
        if verbose:
            print(f"Weighted Refinement Out vs. Out: {out_out_ref:+.2f} (Factor: {weight_out_out:+.2f})")
    else:
        out_out_ref = None

    # Sum up all refinement scores
    refinement = sum(all_refs)

    # Final score is the sum of base score and all refinement terms
    final_score = base_score + refinement

    if verbose:
        print("-" * 80 + "\n")
        print(f"Global refinement average = {refinement:.2f}")
        print(f"Final structuredness score = {final_score:.2f}\n")
        print("=" * 80 + "\n")

    # Collect all activities that are part of any super-block
    block_acts = [act for sb in super_blocks for act in get_super_block_acts(sb)]

    # Format insider and outsider activity sets as strings for output
    insider_str = ",".join(sorted(block_acts)) if block_acts else "-"
    outsider_str = ",".join(sorted(outsiders)) if outsiders else "-"

    # Build output row for CSV or summary table
    row = ([
        path.split("/")[2].split(".")[0],
        reason,
        insider_str,
        outsider_str,
        round(base_score, 3) if base_score else None,
        round(sb_sb_ref, 3) if sb_sb_ref else None,
        round(out_sb_ref, 3) if out_sb_ref else None,
        round(out_out_ref, 3) if out_out_ref else None,
        round(refinement, 3) if refinement else None,
        round(final_score, 3)
    ])

    return final_score, row


if __name__ == "__main__":
    # Load data files
    directory = 'data/synthetic'
    files = sorted([os.path.join(directory, f) for f in os.listdir(directory)])

    # Decide on how much info to display per process
    verbose = True

    # ALL
    files = [
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
        "data/synthetic/Log14_looselyStructured.json",
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
        "data/synthetic/Log26_structured.json",
        "data/synthetic/Log27_semiStructured.json",
        "data/synthetic/Log28_structured.json",
        "data/synthetic/Log29_unstructured.json",
        "data/synthetic/Log30_semiStructured.json",
        #"data/augur.json",
        #"data/chicken.json",
    ]

    # only structured
    """FILES = [
        "data/synthetic/Log01_structured.json",
        "data/synthetic/Log04_structured.json",
        "data/synthetic/Log05_structured.json",
        "data/synthetic/Log12_structured.json",
        "data/synthetic/Log15_structured.json",
        "data/synthetic/Log18_structured.json",
        "data/synthetic/Log19_structured.json"
    ]"""

    # only semi-structured
    """FILES = [
        "data/synthetic/Log02_semiStructured.json",
        "data/synthetic/Log06_semiStructured.json",
        "data/synthetic/Log07_semiStructured.json",
        "data/synthetic/Log10_semiStructured.json",
        "data/synthetic/Log13_semiStructured.json",
        "data/synthetic/Log17_semiStructured.json",
        "data/synthetic/Log20_semiStructured.json",
        "data/synthetic/Log30_semiStructured.json",
    ]"""

    # only loosely structured
    """FILES = [
        "data/synthetic/Log03_looselyStructured.json",
        "data/synthetic/Log08_looselyStructured.json",
        "data/synthetic/Log11_looselyStructured.json",    
        "data/synthetic/Log03_looselyStructured.json",
        "data/synthetic/Log08_looselyStructured.json",
        "data/synthetic/Log11_looselyStructured.json",
        "data/synthetic/Log14_looselySemiStructured.json",
        "data/synthetic/Log16_looselyStructured.json",
        "data/synthetic/Log21_looselyStructured.json",
        "data/synthetic/Log22_looselyStructured.json",
        "data/synthetic/Log23_looselyStructured.json",
        "data/synthetic/Log24_looselyStructured.json",
        "data/synthetic/Log29_unstructured.json"
    ]"""

    """files = [
        "data/synthetic/Log13_semiStructured.json"
    ]"""
    
    #files.remove("data/synthetic/Log07_semiStructured.json")

    # Score each file and aggregate results
    summary_rows = []
    for f in files:
        final_score, row = score_process(f, verbose)
        summary_rows.append(row)

    # print table of all results
    print(tabulate(
        summary_rows,
        headers=[
            "File",
            "SB",
            "Insiders",
            "Outsiders",
            "Base-Score",
            #"SBs (intra)",
            "SB vs. SB",
            "Out vs. SB",
            "Out vs. Out",
            "Refinement",
            "Score"
        ],
        tablefmt="grid"
    ))

