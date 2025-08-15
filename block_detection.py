from itertools import combinations, permutations
from collections import defaultdict, Counter
from collections import defaultdict
import random
from utils import flatten_blocks, flatten_block, earliest_among, latest_among, find_first_allowed_pred, flatten_block_acts

def build_super_blocks(blocks, relationships):
    """
    Combines related control-flow blocks into larger super-blocks based on temporal relations.

    Blocks are combined if they follow each other directly in time or share a common boundary activity.
    The result is a non-overlapping decomposition of the process into larger, coherent fragments, i.e., super-blocks.

    Args:
        blocks (List[Dict]): List of individual control-flow blocks with fields:
            - "start": start activity of block (may be None)
            - "end": end activity of block (may be None)
            - "activities": list of activities (may include tuples)
        relationships (Dict[str, Dict[str, str]]): Pairwise temporal+existential relationships between activities,
            encoded as strings like "<d,=>" or "-,<=>" for each activity pair.

    Returns:
        List[Dict]: List of super-blocks. Each super-block is a dictionary containing:
            - "start": overall start activity of the combined fragment
            - "end": overall end activity of the combined fragment
            - "activities": list of all inner activities (flattened, deduplicated)
    """

    all_acts = list(relationships.keys())

    # Preprocess pairwise temporal relations from relationships
    temporal = {
        a: {b: ("-" if a == b else relationships[a][b].split(",")[0]) for b in all_acts}
        for a in all_acts
    }

    # Identify edges between blocks, i.e., how the blocks will be arranged as super-blocks
    edges = []

    for i, block_i in enumerate(blocks):
        for j, block_j in enumerate(blocks):
            if i >= j:
                continue

            # Flatten inner activities for fallback
            inner_i = flatten_block_acts(block_i)
            inner_j = flatten_block_acts(block_j)

            # Case 1: Edge from i to j
            # Determine start and end of blocks if available, else use inner acts
            ends_i = [block_i["end"]] if block_i.get("end") else inner_i
            starts_j = [block_j["start"]] if block_j.get("start") else inner_j

            # Either direct temporal relationship from end of i to start of j, or they are the same activity
            if any(temporal[e][s] == "<d" for e in ends_i for s in starts_j) or \
               any(e == s for e in ends_i for s in starts_j):
                edges.append((i, j))
                continue

            # Case 2: Edge from j to i
            # Determine start and end of blocks if available, else use inner acts
            ends_j = [block_j["end"]] if block_j.get("end") else inner_j
            starts_i = [block_i["start"]] if block_i.get("start") else inner_i

            # Either direct temporal relationship from end of j to start of i, or they are the same activity
            if any(temporal[e][s] == "<d" for e in ends_j for s in starts_i) or \
               any(e == s for e in ends_j for s in starts_i):
                edges.append((j, i))


    # Initialize maps to store incoming and outgoing edges for each block index
    incoming = defaultdict(set) 
    outgoing = defaultdict(set)

    for source_idx, target_idx in edges:
        outgoing[source_idx].add(target_idx)
        incoming[target_idx].add(source_idx)

    # Store final chain, i.e., an ordered list of block indices
    chains = []

    # Track which block indices have already been assigned to a chain
    visited = set()

    for idx in range(len(blocks)):
        # Skip this block if it has already been included in a previous chain
        if idx in visited:
            continue

        # Find the starting point of the chain by following incoming edges backwards
        current = idx
        while incoming[current]:
            current = next(iter(incoming[current]))

        # Build the chain starting from the source
        chain = [current]
        while outgoing[current]:
            current = next(iter(outgoing[current]))
            chain.append(current)

        # Mark all blocks in this chain as visited so they won't be included again
        visited.update(chain)

        # Add the completed chain to the result
        chains.append(chain)

    super_blocks = []

    # Build super-blocks from each chain
    for chain in chains:
        # Combine all activities from all blocks in chain
        blocks_acts = set.union(*[flatten_block(blocks[i]) for i in chain])

        # Determine start/end from first and last block
        start = blocks[chain[0]]["start"]
        end = blocks[chain[-1]]["end"]

        # Remove start/end from inner activities
        if start:
            blocks_acts.discard(start)
        if end:
            blocks_acts.discard(end)

        # Create combined super-block
        super_block = {
            "start": start,
            "end": end,
            "activities": list(blocks_acts) 
        }

        # Avoid duplicate chains
        if super_block not in super_blocks:
            super_blocks.append(super_block)

    return super_blocks


def detect_blocks(relationships):
    """
    Detects all control-flow blocks in a process model based on pairwise activity relations.

    The function identifies the following types of blocks:
    - XOR blocks: exclusive choices between multiple alternative branches.
    - PAR blocks: parallel branches that always co-occur.
    - Optional blocks: single optional activities between two fixed activities.
    - SEQUENCE blocks: linear sequences of activities that always co-occur in fixed order.

    All blocks are derived based on temporal and existential relations between activities.
    Nested structures are cleaned to avoid overlapping or redundant blocks.

    Args:
        relationships (Dict[str, Dict[str, str]]): Mapping from activity pairs 
            to their (temporal, existential) relationship string (e.g., "<,=>").

    Returns:
        List[Dict]: A list of detected block structures. Each block contains:
            - "block_type": one of {"XOR", "PAR", "SEQUENCE"}
            - "activities": the grouped activities or branches
            - "start": the split activity (if applicable)
            - "end": the merge activity (if applicable)
            - "nested": any nested blocks (if present)
    """
    acts = list(relationships.keys())

    # Shuffle to prevent artifacts caused by activity ordering
    random.shuffle(acts)

    # Extract pairwise temporal and existential relations for all activity pairs
    temporal = {
        a: {b: ("-" if a == b else relationships[a][b].split(",")[0]) for b in acts}
        for a in acts
    }
    existential = {
        a: {b: ("-" if a == b else relationships[a][b].split(",")[1]) for b in acts}
        for a in acts
    }

    # Initialize (direct) predecessor/successor dictionaries
    preds = {a: set() for a in acts}
    succs = {a: set() for a in acts}
    direct_preds = {a: set() for a in acts}
    direct_succs = {a: set() for a in acts}

    # Build (direct) successor/predecessor relations
    for a, b in combinations(acts, 2):
        if "<" in temporal[a][b]:
            succs[a].add(b)
            preds[b].add(a)
            if "d" in temporal[a][b]: 
                direct_succs[a].add(b)
                direct_preds[b].add(a)
        if "<" in temporal[b][a]:
            succs[b].add(a)
            preds[a].add(b)
            if "d" in temporal[b][a]:
                direct_succs[b].add(a)
                direct_preds[a].add(b)


    # Precompute (non-)co-occurrence flags
    always = {
        a: {b: (temporal[a][b]=="-" and existential[a][b]=="<=>") for b in acts}
        for a in acts
    }
    never  = {
        a: {b: (temporal[a][b]=="-" and existential[a][b]=="</=>") for b in acts}
        for a in acts
    }

    # Identify XOR blocks
    xor_blocks = get_xor_blocks(
        acts, preds, succs, direct_preds, direct_succs, temporal, existential, always, never
    )

    # Identify PAR blocks
    par_blocks = get_par_blocks(
        acts, preds, succs, direct_preds, direct_succs, temporal, existential, always, never
    )

    # Identify optional blocks
    optional_blocks = get_optional_blocks(acts, xor_blocks, succs, temporal, existential)

    # Identify sequence blocks 
    seq_blocks = get_sequences(acts, direct_succs, existential)

    # Remove redundant blocks caused by XOR/PAR nesting
    xor_blocks_clean = remove_duplicate_blocks_from_nesting(xor_blocks, par_blocks)
    par_blocks_clean = remove_duplicate_blocks_from_nesting(par_blocks, xor_blocks)
    seq_blocks_clean = remove_duplicate_blocks_from_nesting(seq_blocks, xor_blocks, include_split_merge=True)
    seq_blocks_clean = remove_duplicate_blocks_from_nesting(seq_blocks_clean, par_blocks, include_split_merge=True)

    # Combine all block types into a unified structure list
    blocks = xor_blocks_clean + par_blocks_clean + optional_blocks + seq_blocks_clean

    return blocks


def get_xor_blocks(acts, preds, succs, direct_preds, direct_succs, temporal, existential, always, never):
    """
    Identifies XOR blocks within a process model based on binary relations between activities.

    The algorithm iterates over all activities and attempts to construct XOR blocks by finding mutually
    exclusive execution paths. It supports nested structures and accounts for embedded PAR blocks and further nesting.

    Steps performed by the function:
    1. For each activity x, find all other activities y such that x and y never co-occur.
    2. Construct branches starting from x and its XOR partners using temporal and existential conditions.
    3. Detect nested PAR blocks within branches and tag branches as XOR or PAR.
    4. Identify a possible merge activity that appears in all branches and follows them.
    5. Remove invalid successors from branches if the XOR exclusiveness criterion is violated.
    6. Identify a split activity if one exists. Must be a shared direct predecessor of all branches (except PAR branches).
    7. Store the block with its start (split), end (merge), activities, and nested block structures.
    8. Remove redundant blocks that are subsets of other blocks.
    9. Remove blocks with duplicated activities across XOR blocks (to ensure exclusiveness).

    Args:
        acts (List[str]): List of all activity labels in the process.
        preds (Dict[str, List[str]]): Predecessor relation mapping for each activity.
        succs (Dict[str, List[str]]): Successor relation mapping for each activity.
        direct_preds (Dict[str, Set[str]]): Direct predecessors per activity.
        direct_succs (Dict[str, Set[str]]): Direct successors per activity.
        temporal (Dict[str, Dict[str, str]]): Temporal relations between activities (e.g., "<", ">").
        existential (Dict[str, Dict[str, str]]): Existential relations between activities (e.g., "</=>").
        always (Dict[str, Dict[str, bool]]): True if two activities always co-occur.
        never (Dict[str, Dict[str, bool]]): True if two activities never co-occur.

    Returns:
        List[Dict]: A list of XOR blocks, each represented as a dictionary with:
            - "block_type": "XOR"
            - "activities": List of tuples or strings (branches)
            - "nested": List of nested PAR blocks (if any)
            - "start": Split activity (or None)
            - "end": Merge activity (or None)
    """
    xor_blocks = []
    for x in acts:
        # all acts y with x XOR y
        acts_XOR_x = [
                y for y in acts
                if y!=x
                and never[x][y]
            ]

        # continue with next act if no XOR exists
        if len(acts_XOR_x) == 0:
            continue

        # branches in XOR containing the acts
        branches = []

        # store if branches are XOR or PAR to identify later
        branch_encoding = []

        # not yet used acts in any branch
        remaining_XOR_acts = [x] + acts_XOR_x

        while len(remaining_XOR_acts) > 0:
            # For an element of acts, get the first element within XOR acts
            y = find_first_allowed_pred(next(iter(remaining_XOR_acts)), preds, remaining_XOR_acts)

            # this branch contains all acts that follow the first element within branch
            new_branch = append_branch_succs(y, succs, temporal, existential, type="XOR")

            # Add potential PAR acts if this branch contains a PAR split
            acts_par_y = [other for other in acts if always[y][other]]

            branches += [new_branch + acts_par_y]

            if len(acts_par_y) > 0:
                branch_encoding += ["PAR"]
            else:
                branch_encoding += ["XOR"]

            # continue with acts in other branches (in XOR to y)
            remaining_XOR_acts = [
                z for z in remaining_XOR_acts
                if never[y][z]
            ]

        # get PAR blocks from nested PAR acts for later usage
        # reduce acts to only current block we're looking at
        branches_acts = set([act for branch in branches for act in branch])
        nested_par_blocks = get_par_blocks(branches_acts, preds, succs, direct_preds, direct_succs, temporal, existential, always, never)

        # Check for merge acts and clean up branches
        merge = None
        joint_acts = set(branches[0]).intersection(*[set(b) for b in branches[1:]])
        if joint_acts:
            # Remove all joint acts from branches, they are outside of branch
            branches = [
                [x for x in branch if x not in joint_acts]
                for branch in branches
            ]
            merge_cands = earliest_among(joint_acts, succs)
            # if a single joint act exists, it's the merge act
            if len(merge_cands) == 1:
                merge = next(iter(merge_cands))

        # Further clean up for XOR
        # What always has to hold: all elements in branches are XOR to each other
        xor_criterium = True
        for b1 in branches:
            for b2 in branches:
                if b1 == b2:
                    continue
                xor_criterium = all([existential[a1][a2] == "</=>" for a1 in b1 for a2 in b2])
                if not xor_criterium:
                    break
            if not xor_criterium:
                    break
        
        # if it doesn't hold, there have to be succs added to branch that don't fulfill criterium
        # therefore, find smallest subset with acts in branches that fulfill condition
        if not xor_criterium:
            branches = reduce_branches_to_only_XOR(branches, preds, existential)

        # Find split act if it exists
        # if split act before XOR exists, it's the single joint direct pred of first element of all branches
        first_elements = [branch[0] for branch in branches]
        direct_pred_sets = [direct_preds[elem] for elem in first_elements]
        split = None
        if (
            len(direct_pred_sets[0]) > 0 
            and all(p == direct_pred_sets[0] for p in direct_pred_sets)
            # make sure not multiple direct preds exists, then it's no split activity
            and len(direct_pred_sets[0]) == 1
        ):
            split = next(iter(direct_pred_sets[0]))
        # Exception: If PAR is nested within XOR, there is no direct relationship between XOR split and PAR acts
        elif (len(nested_par_blocks) > 0
            and any([len(pred_set) > 0 for pred_set in direct_pred_sets])
        ):
            encoding = [True if enc == "XOR" else False for enc in branch_encoding]
            xor_preds = [x for x, m in zip(direct_pred_sets, encoding) if m]
            # Use direct pred from XOR as start if all XOR direct preds are equal 
            if len(xor_preds[0]) > 0 and all(s == xor_preds[0] for s in xor_preds):
                split = next(iter(next(iter(xor_preds))))

    
        block_acts = [tuple(branch) if len(branch) > 1 else branch[0] for branch in branches]

        # sort block acts for reproducability
        strings = sorted([x for x in block_acts if isinstance(x, str)])
        tuples = sorted(
            [tuple(sorted(t)) for t in block_acts if isinstance(t, tuple)],
            key=lambda t: t
        )

        xor_blocks.append({
            "block_type": "XOR",
            "activities": strings + tuples,
            "nested": nested_par_blocks,
            "start": split, 
            "end": merge
        })

    # Remove redundant XOR-Blocks
    filtered_xor_blocks = remove_redundant_blocks(xor_blocks)

    # Remove incorrectly identified XOR-blocks
    # -> blocks that contain identical act entries (shouldn't happen, if that's actually the case they are in one block combined)
    all_activities = []
    for block in filtered_xor_blocks:
        all_activities.extend(block['activities'])

    activity_counts = Counter(all_activities)

    final_xor_blocks = [
        block for block in filtered_xor_blocks
        if all(activity_counts[act] == 1 for act in block['activities'])
    ]

    return final_xor_blocks


def get_par_blocks(acts, preds, succs, direct_preds, direct_succs, temporal, existential, always, never):
    """
    Identifies PAR blocks within a process model based on binary relations between activities.

    The algorithm iterates over all activities and attempts to construct PAR blocks by finding groups of 
    activities that always co-occur. It supports nested structures and accounts for embedded XOR blocks 
    and further nesting.

    Steps performed by the function:
    1. For each activity x, find all other activities y such that x and y always co-occur.
    2. Construct branches starting from x and its PAR partners using temporal and existential conditions.
    3. Add any XOR activities that follow the branch head but are mutually exclusive with it.
    4. Identify a possible merge activity that appears in all branches and follows them.
       If multiple candidates exist, select the one with appropriate existential relations to all branch activities.
    5. Identify a split activity if one exists. Must be the latest shared predecessor of all branch starts.
       The split must have (<, <=>) relations to all PAR activities in the block.
    6. Detect nested XOR blocks within the PAR structure using the previously defined XOR detection algorithm.
       This is done after merge cleanup to avoid including unrelated XOR blocks beyond the PAR boundary.
    7. Store the block with its start (split), end (merge), activities, and nested block structures.
    8. Remove redundant blocks that are subsets of other blocks.
    9. Remove blocks with duplicated activities across PAR blocks (to ensure exclusiveness).

    Args:
        acts (List[str]): List of all activity labels in the process.
        preds (Dict[str, List[str]]): Predecessor relation mapping for each activity.
        succs (Dict[str, List[str]]): Successor relation mapping for each activity.
        direct_preds (Dict[str, Set[str]]): Direct predecessors per activity.
        direct_succs (Dict[str, Set[str]]): Direct successors per activity.
        temporal (Dict[str, Dict[str, str]]): Temporal relations between activities (e.g., "<", ">").
        existential (Dict[str, Dict[str, str]]): Existential relations between activities (e.g., "<=>", "=>").
        always (Dict[str, Dict[str, bool]]): True if two activities always co-occur.
        never (Dict[str, Dict[str, bool]]): True if two activities never co-occur.

    Returns:
        List[Dict]: A list of PAR blocks, each represented as a dictionary with:
            - "block_type": "PAR"
            - "activities": List of tuples or strings (branches)
            - "nested": List of nested XOR blocks (if any)
            - "start": Split activity (or None)
            - "end": Merge activity (or None)
    """
    par_blocks = []
    for x in acts:
        # all acts y with x PAR y
        acts_PAR_x = [
                y for y in acts
                if y!=x
                and always[x][y]
        ]

        # continue with next act if no XOR exists
        if len(acts_PAR_x) == 0:
            continue

        # branches in PAR containing the acts
        branches = []

        # not yet used acts in any branch
        remaining_PAR_acts = [x] + acts_PAR_x

        while len(remaining_PAR_acts) > 0:
            # For an element of acts, get the first element within PAR acts
            y = find_first_allowed_pred(next(iter(remaining_PAR_acts)), preds, remaining_PAR_acts)

            # this branch contains all acts that follow the first element within branch
            new_branch = append_branch_succs(y, succs, temporal, existential, type="PAR")

            # Add potential XOR acts if this branch contains an XOR split
            y_xor_acts = [other for other in acts if never[y][other]]

            branches += [new_branch + y_xor_acts]
            
            # remove used act in this iteration and continue with remaining acts
            remaining_PAR_acts = [
                z for z in remaining_PAR_acts
                if y!=z
                and always[y][z]
            ]

        # Get acts in branches that are part of a nested XOR for later usage
        branches_acts = set([act for branch in branches for act in branch])
        nested_xor_acts = set([
            x for x in branches_acts for y in branches_acts
            if never[x][y]
        ])

        # Check for merge acts and clean up branches
        merge = None
        joint_acts = set(branches[0]).intersection(*[set(b) for b in branches[1:]])
    
        if joint_acts:
            # Remove all joint acts from branches, they are outside of branch
            branches = [
                [x for x in branch if x not in joint_acts]
                for branch in branches
            ]
            merge_cands = earliest_among(joint_acts, succs)
            # if multiple merge acts exist, check if there is a single one with <=> (for PAR acts) or <= (for XOR acts) 
            # existential relationship to branch acts -> This is merge
            for merge_cand in merge_cands:
                if all(existential[merge_cand][x] in ("<=", "<=>") for x in [act for branch in branches for act in branch]):
                    merge = merge_cand

        # Find split act if it exists
        # if split act before PAR exists, it's the latest joint pred of first element of all branches
        first_elements = [branch[0] for branch in branches]
        pred_sets = [preds[elem] for elem in first_elements]
        split = None
        if (
            len(pred_sets[0]) > 0 
            and all(p == pred_sets[0] for p in pred_sets)):
            # Get all latest preds of each branch
            start_candidates = [next(iter(latest_among(s, succs))) for s in pred_sets]
            # Latest pred of each branch should be same activitiy if it is the split act
            if len(set(start_candidates)) == 1:
                start_candidate = start_candidates[0]
                split = start_candidate

                # Further check if identified split is really a correct split act
                # Relationship between all PAR acts in branch and split has to be (<, <=>)
                # Remove nested XOR as here relationship becomes (<,<=)
                par_branch_acts = {par_act for branch in branches for par_act in branch} - set(nested_xor_acts)
                # If (<, <=>) relationship doesn't hold for any PAR act, split is incorrect
                for par_act in par_branch_acts:
                    if not(temporal[start_candidate][par_act] == "<" 
                        and existential[start_candidate][par_act] == "<=>"):
                        split = None
                        break

        # get XOR blocks from nested XOR acts
        # reduce acts to only current block we're looking at
        branches_acts = set([act for branch in branches for act in branch])

        nested_XOR_blocks = get_xor_blocks(branches_acts, preds, succs, direct_preds, direct_succs, temporal, existential, always, never)

        block_acts = [tuple(branch) if len(branch) > 1 else branch[0] for branch in branches]

        # sort block acts for reproducability
        strings = sorted([x for x in block_acts if isinstance(x, str)])
        tuples = sorted(
            [tuple(sorted(t)) for t in block_acts if isinstance(t, tuple)],
            key=lambda t: t
        )

        par_blocks.append({
            "block_type": "PAR",
            "activities": strings + tuples,
            "nested": nested_XOR_blocks,
            "start": split, 
            "end": merge
        })

    
    # Remove redundant PAR-Blocks
    filtered_par_blocks = remove_redundant_blocks(par_blocks)

    # Remove incorrectly identified PAR-blocks
    # -> blocks that contain identical act entries (shouldn't happen, if that's actually the case they are in one block combined)
    all_activities = []
    for block in filtered_par_blocks:
        all_activities.extend(block['activities'])

    activity_counts = Counter(all_activities)

    final_par_blocks = [
        block for block in filtered_par_blocks
        if all(activity_counts[act] == 1 for act in block['activities'])
    ]

    return final_par_blocks


def get_optional_blocks(acts, xor_blocks, succs, temporal, existential):
    """
    Identifies optional XOR blocks in the process model.

    An optional block is a structure where:
    - A block activity z is conditionally executed between two activities x and y.
    - The following relations must hold:
        * (x, y):        temporal = "<", existential = "<=>"
        * (x, z):        temporal = "<", existential = "<="
        * (z, y):        temporal = "<", existential = "=>"
    - The activity z must not already be part of an XOR block.

    Steps:
    1. Iterate over all activity pairs (x, y) that always co-occur in a strict order.
    2. For each such pair, search for intermediate activity z that fits the optional execution pattern.
    3. Exclude blocks where x, z, or y are already part of known XOR blocks.
    4. Deduplicate blocks that share the same z activity by preferring:
        a) The block with the earliest merge.
        b) Among those, the block with the latest split.

    Args:
        acts (List[str]): All activities in the process.
        xor_blocks (List[Dict]): Already identified XOR blocks (to avoid overlaps).
        succs (Dict[str, Set[str]]): Successors of each activity.
        temporal (Dict[str, Dict[str, str]]): Temporal relations between activities (e.g., "<").
        existential (Dict[str, Dict[str, str]]): Existential relations between activities (e.g., "<=>", "=>").

    Returns:
        List[Dict]: Cleaned list of optional blocks.
    """
    opt_blocks = []
    for x in acts:
        for y in acts:
            # Check if x and y always co-occur in fixed order
            if temporal[x][y] == "<" and existential[x][y] == "<=>":
                for z in acts:
                    # Check if z fits the optional structure pattern
                    if ("<" in temporal[x][z]
                        and existential[x][z] == "<="
                        and "<" in temporal[z][y]
                        and existential[z][y] == "=>"):

                        # Flatten XOR blocks for duplicate checking
                        block_acts_flat = flatten_blocks(xor_blocks)

                        # Ensure x, z, or y are not already part of an XOR block
                        if not any(act in block_acts_flat for act in [x, y, z]):
                            opt_blocks.append({
                                "block_type": "OPTIONAL",
                                "activities": [z],
                                "nested": [],
                                "start": x,
                                "end": y
                            })

    opt_blocks_clean = []
    visited = []

    for i, block_i in enumerate(opt_blocks):
        # Skip if already handled
        if i in visited:
            continue

        opt_blocks_duplicates = [block_i]
        for j, block_j in enumerate(opt_blocks[i+1:], start=i+1):
            if block_i["activities"] == block_j["activities"]:
                opt_blocks_duplicates.append(block_j)
                visited.append(j)

        # If no opt_blocks_duplicates, keep block_i as-is
        if len(opt_blocks_duplicates) == 1:
            opt_blocks_clean.append(block_i)
            continue

        # Step 1: pick block(s) with earliest merge
        merges = [b["end"] for b in opt_blocks_duplicates]
        earliest_merges = earliest_among(merges, succs)
        candidates = [b for b in opt_blocks_duplicates if b["end"] in earliest_merges]

        # If this leads to one single block, we are done
        if len(candidates) == 1:
            opt_blocks_clean.append(candidates[0])
            continue

        # Step 2: among those, pick one with latest split
        splits = [b["start"] for b in candidates]
        latest_splits = latest_among(splits, succs)

        for b in candidates:
            if b["start"] in latest_splits:
                opt_blocks_clean.append(b)
                break

    return opt_blocks_clean


def get_sequences(acts, direct_succs, existential):
    """
    Identifies SEQUENCE blocks in the process model.

    A SEQUENCE block is a structure where:
    - A set of activities are directly connected and always co-occur in the same strict temporal order.
    - Each activity has exactly one direct successor with:
        * (a, b): existential = "<=>"
    - Only sequences of length ≥ 2 are considered.
    - Activities can appear in only one sequence block.

    Steps:
    1. Iterate over all activities and identify chains of direct successors.
    2. For each valid pair (a, b), check if they always co-occur in fixed order (<=>).
    3. Extend the chain forward as long as the co-occurrence condition holds.
    4. Store the sequence with start and end activities, excluding the inner activities.
    5. Filter out redundant sequences where all activities are subsets of a longer sequence.

    Args:
        acts (List[str]): All activities in the process.
        direct_succs (Dict[str, Set[str]]): Direct successors of each activity.
        existential (Dict[str, Dict[str, str]]): Existential relations between activities (e.g., "<=>").

    Returns:
        List[Dict]: Cleaned list of SEQUENCE blocks.
    """

    sequences = []
    # Activities already assigned to a sequence
    visited = set()

    for x in acts:
        # Skip if already part of a sequence
        if x in visited:
            continue  

        sequence = [x]
        current = x

        # Walk forward through direct successors
        while True:
            next_acts = direct_succs[current]
            # No more successors
            if not next_acts:
                break 

            y = next(iter(next_acts))
            # Check if current and next always co-occur
            if existential[current][y] == "<=>":
                sequence.append(y)
                current = y
            # Else, end of sequence
            else:
                break 

        # Only add sequence if non-trivial (at least 2 elements)
        if len(sequence) > 1:
            visited.update(sequence)
            sequences.append({
                "block_type": "SEQUENCE",
                "activities": sequence[1:-1],
                "nested":     [],
                "start":      sequence[0],
                "end":        sequence[-1]
            })

    # Remove overlapping or redundant sequences
    full_acts = [flatten_block(seq) for seq in sequences]
    keep = [True] * len(sequences)

    for i in range(len(full_acts)):
        for j in range(len(full_acts)):
            # i is a subset of j -> drop it
            if i != j and full_acts[i] < full_acts[j]:
                keep[i] = False  
                break

    sequences_clean = [seq for seq, k in zip(sequences, keep) if k]

    return sequences_clean



def remove_duplicate_blocks_from_nesting(blocks_to_clean, ref_blocks, include_split_merge=False):
    blocks_cleaned = []
    for block in blocks_to_clean:
        duplicate = False
        for ref_block in ref_blocks:
            block_acts = flatten_block(block, include_split_merge)
            ref_block_acts = flatten_block(ref_block, include_split_merge)

            if all([block_act in ref_block_acts for block_act in block_acts]):
                duplicate = True
                break
        if not duplicate:
            blocks_cleaned.append(block)

    return blocks_cleaned


def remove_redundant_blocks(blocks):
    """
    Removes redundant XOR blocks based on their 'activities' field.
    For blocks with identical activities, the one with more structure (i.e., 'start' or 'end') is preferred.
    Then removes blocks whose activities are a proper subset of another block's activities.
    
    Args:
        blocks (List[Dict]): List of XOR blocks
    
    Returns:
        List[Dict]: Cleaned list of non-redundant XOR blocks
    """
    seen = {}
    unique_blocks = []

    for block in blocks:
        # Create a key based on sorted activities
        acts = block['activities']
        acts_key = tuple(sorted(
            tuple(sorted(act)) if isinstance(act, tuple) else (act,)
            for act in acts
        ))

        # Decide whether to store/replace this block
        if acts_key not in seen:
            seen[acts_key] = block
        else:
            existing = seen[acts_key]
            # Prefer block with defined 'start' or 'end'
            existing_score = int(existing.get('start') is not None) + int(existing.get('end') is not None)
            current_score = int(block.get('start') is not None) + int(block.get('end') is not None)
            if current_score > existing_score:
                seen[acts_key] = block

    # Use only the most informative representative for each activity set
    unique_blocks = list(seen.values())

    # Precompute flattened activity sets for all blocks
    flattened_blocks = [flatten_block(block, include_split_merge=False) for block in unique_blocks]

    keep = [True] * len(unique_blocks)

    # Remove blocks that are strict subsets of others
    for i, acts_i in enumerate(flattened_blocks):
        for j, acts_j in enumerate(flattened_blocks):
            if i == j:
                continue
            if acts_i < acts_j:
                keep[i] = False
                break

    return [block for block, keep_flag in zip(unique_blocks, keep) if keep_flag]


def find_best_xor_assignment(branches, preds, existential):
    """
    Cleans up a list of branches by removing activities that violate the XOR condition:
    For every pair of activities across different branches, the existential relationship
    must be '</=>'. Activities that appear in multiple branches are exempt from this check.
    
    The function removes activities from the end of branches until the condition holds.
    """
    # Sort activities in each branch based on control-flow dependencies
    sorted_branches = [sort_branch_by_preds(branch, preds) for branch in branches]

    def is_valid(assignment):
        """
        Checks whether the given branch assignment satisfies the XOR condition:
        For any pair of activities from different branches, they must be mutually exclusive.
        Shared activities (i.e., appearing in multiple branches) are ignored.
        """
        for i in range(len(assignment)):
            for j in range(i + 1, len(assignment)):
                for act_i in assignment[i]:
                    for act_j in assignment[j]:
                        # skip comparison of same activity
                        if act_i == act_j:
                            continue
                        if act_i in assignment[j] or act_j in assignment[i]:
                            continue
                        if existential[act_i][act_j] != "</=>" or existential[act_j][act_i] != "</=>":
                            return False
        return True
    
    final_branches = [list(branch) for branch in sorted_branches]

    # Remove invalid activities from each branch until XOR condition holds
    for branch in final_branches:
        while not is_valid(final_branches):
            if not branch:
                break
            branch.pop()
        if not branch:
            raise ValueError("No valid XOR assignment found for all branches")

    return final_branches

def sort_branch_by_preds(branch, preds):
    """Sort a single branch based on temporal order given by preds."""
    known = [act for act in branch if act in preds]

    # Build a subgraph for the known activities
    graph = defaultdict(set)
    in_degree = defaultdict(int)
    for act in known:
        for pred in preds[act]:
            if pred in known:
                graph[pred].add(act)
                in_degree[act] += 1

    # Topological sort
    ordered = []
    queue = [act for act in known if in_degree[act] == 0]
    while queue:
        node = queue.pop(0)
        ordered.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Add any remaining nodes in original order
    remaining = [act for act in known if act not in ordered]
    ordered.extend(remaining)

    return ordered + [act for act in branch if act not in preds]

def reduce_branches_to_only_XOR(branches, preds, existential):
    """
    Applies XOR cleanup to all permutations of branch order and selects the result
    with the highest total number of activities. This ensures minimal information loss
    while enforcing XOR constraints.
    """
    best_result = None
    max_total_activities = -1

    for perm in permutations(branches):
        try:
            reduced = find_best_xor_assignment(perm, preds, existential)
            total_activities = sum(len(branch) for branch in reduced)
            if total_activities > max_total_activities:
                max_total_activities = total_activities
                best_result = reduced
        except ValueError:
            continue

    return best_result

def append_branch_succs(start, succs, temporal, existential, type):
    # chain of sequences
    xor_succs = [start]
    # starting activitiy
    acts_to_explore = [start]
    explored_acts = []

    if type == "XOR":
        allowed_temp = ["<", "<d"]
        allowed_exist = ["<=", "=>", "<=>"]
    elif type == "PAR":
        allowed_temp = ["<"]
        allowed_exist = ["<=", "<=>"]
    else:
        raise RuntimeError(f"Type {type} unknown for appending branch successors")

    while len(acts_to_explore) > 0:
        for act in acts_to_explore.copy():
            for x in succs[act]:
                # identify next sequence activity
                if temporal[act][x] in allowed_temp and existential[act][x] in allowed_exist:
                    if not x in acts_to_explore and not x in explored_acts:
                        acts_to_explore.append(x)
                    if not x in xor_succs:
                        xor_succs.append(x)
            explored_acts.append(act)
                    
        acts_to_explore.remove(act)
    return xor_succs