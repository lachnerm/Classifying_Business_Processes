
from itertools import combinations
from utils import get_super_block_acts
import math
from constants import REFINEMENT_SCORES_OUT_TO_OUT, REFINEMENT_SCORES_OUT_TO_SB, REFINEMENT_SCORES_SB_TO_SB
from warnings import warn

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
        n_sbs_str (str): Explanation string summarizing number of super-blocks.
    """

    # Convert activity list to set for faster lookups
    all_acts_set = set(all_acts)

    # Collect all activities that are covered by any super-block (including start/end)
    covered_acts = set()
    for sb in super_blocks:
        covered_acts.update(sb["activities"])
        if sb["start"]:
            covered_acts.add(sb["start"])
        if sb["end"]:
            covered_acts.add(sb["end"])

    # Identify uncovered activities
    outsider_acts = all_acts_set - covered_acts
    total_activity_count = len(all_acts_set)

    # Compute coverage fraction for each super-block
    coverage_fractions = []

    # Store acts already included in other super-blocks to avoid computing duplicate coverages
    already_covered = set()
    for sb in super_blocks:
        covered_in_block = sb["activities"].copy()
        if sb["start"]:
            covered_in_block.append(sb["start"])
        if sb["end"]:
            covered_in_block.append(sb["end"])

        covered_clean = set(covered_in_block) - already_covered
        already_covered.update(set(covered_in_block))

        coverage_fraction = len(covered_clean) / total_activity_count if total_activity_count else 0.0
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
        n_sbs_str = "0 SB"
    elif num_blocks == 1:
        n_sbs_str = "1 SB"
    else:
        n_sbs_str = f"{num_blocks} SB"

    return base_score, outsider_acts, n_sbs_str


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
            end_acts = [sb1["end"]] if sb1["end"] else sb1["activities"]
            # Use defined start activities if available, else fall back to internal activities
            start_acts = [sb2["start"]] if sb2["start"] else sb2["activities"]

            if verbose:
                print(f"\nSB{idx1+1}→SB{idx2+1}: end {end_acts} → start {start_acts}")

            # For each combination of end→start activities, look up relation score
            for end in end_acts:
                for start in start_acts:
                    temp, exist = relations[end][start].split(",")
                    score = REFINEMENT_SCORES_SB_TO_SB.get((temp, exist))
                    if not score:
                        warn(f"Unknown relation ({temp},{exist}) for ({end},{start}) - falling back to value 0")
                        score = 0
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
                    warn(f"Unknown relation ({temp},{exist}) for ({outsider},{act}) - falling back to value 0")
                    score = 0

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
            warn(f"Unknown relation ({temp},{exist}) for ({out1},{out2}) - falling back to value 0")
            score = 0
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

def score_process(path, relationships, super_blocks, verbose=False):
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
            n_sbs_str string (e.g., "3 SB"),
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


    # Get the full list of activities from the relationship data
    all_acts = set(relationships.keys())

    # Compute the base structuredness score based on coverage and fragmentation
    base_score, outsiders, n_sbs_str = compute_base_score(super_blocks, all_acts)

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
    block_acts = set([act for sb in super_blocks for act in get_super_block_acts(sb)])

    return final_score, (n_sbs_str, block_acts, outsiders, base_score, sb_sb_ref, out_sb_ref, out_out_ref, refinement)
