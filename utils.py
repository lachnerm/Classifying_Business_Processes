import json

def load_relationships(path):
    """
    Load activity relationship data from a JSON file.
    
    Args:
        path (str or Path): Path to the JSON file containing activity relationships.
    
    Returns:
        dict: Parsed JSON data representing relationships between activities.
    """
    with open(path) as fh:
        relationships = json.load(fh)
    return relationships


def flatten_blocks(blocks, include_split_merge=True):
    """
    Flatten a list of blocks into a single set of activity names.
    
    Args:
        blocks (list): List of block dicts.
        include_split_merge (bool): If True, include block start/end nodes.
    
    Returns:
        set: Union of activities from all blocks.
    """
    block_list = [flatten_block(block, include_split_merge) for block in blocks]
    return set.union(*block_list) if block_list else []


def flatten_block(block, include_split_merge=True):
    """
    Flatten a single block into a set of activity names.
    
    Args:
        block (dict): Block definition containing activities, start, and end.
        include_split_merge (bool): If True, include start/end nodes.
    
    Returns:
        set: Activities in this block (and optionally start/end).
    """
    acts = flatten_block_acts(block)
    if include_split_merge:
        split = block['start']
        merge = block['end']
        if split:
            acts.add(split)
        if merge:
            acts.add(merge)
    return acts


def flatten_block_acts(block):
    """
    Flatten the 'activities' field of a block into a set of strings.
    Handles tuples in 'activities' (e.g., parallel branches) by expanding them.
    
    Args:
        block (dict): Block containing 'activities'.
    
    Returns:
        set: All activities inside the block.
    """
    return {
        elem
        for item in block['activities']
        for elem in (item if isinstance(item, tuple) else (item,))
    }


def latest_among(nodes, succ):
    """
    Find the latest nodes among a set of nodes in a successor graph.
    A node is 'latest' if no other node in the set is reachable from it.
    
    Args:
        nodes (set): Nodes to check.
        succ (dict): Mapping of node → set/list of successors.
    
    Returns:
        set: Subset of nodes that are latest.
    """
    return {n for n in nodes if not any(m in succ[n] for m in nodes if m != n)}


def earliest_among(nodes, succ):
    """
    Find the earliest nodes among a set of nodes in a successor graph.
    A node is 'earliest' if it cannot be reached from any other node in the set.
    
    Args:
        nodes (set): Nodes to check.
        succ (dict): Mapping of node → set/list of successors.
    
    Returns:
        set: Subset of nodes that are earliest.
    """
    return {n for n in nodes if not any(n in succ[m] for m in nodes if m != n)}


def find_first_allowed_pred(x, preds, allowed_preds):
    """
    Find the first predecessor of a node that is in the allowed set.
    Traverses backwards through the predecessor graph until:
      - an allowed predecessor is found with no further predecessors, or
      - no allowed predecessor is found (returns the original node).
    
    Args:
        x (str): Current activity/node.
        preds (dict): Mapping of node → list of predecessors.
        allowed_preds (set): Set of allowed predecessor nodes.
    
    Returns:
        str: First allowed predecessor found, or original node.
    """
    if x in allowed_preds and not preds.get(x):
        return x

    for p in preds.get(x, []):
        if p in allowed_preds:
            return find_first_allowed_pred(p, preds, allowed_preds)
    return x


def get_super_block_acts(super_block):
    """
    Get all activities from a super-block, including start and end nodes.
    
    Args:
        super_block (dict): Super-block definition containing activities, start, and end.
    
    Returns:
        list: List of activity names.
    """
    acts = list(super_block["activities"])
    if super_block["start"]:
        acts.append(super_block["start"])
    if super_block["end"]:
        acts.append(super_block["end"])
    return acts
