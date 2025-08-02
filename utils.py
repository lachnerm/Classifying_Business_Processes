import json

def load_relationships(path):
    with open(path) as fh:
        relationships = json.load(fh)
    return relationships


def find_first_allowed_pred(x, preds, allowed_preds):
    if x in allowed_preds and not preds.get(x):
        return x

    for p in preds.get(x, []):
        if p in allowed_preds:
            print(p)
            return find_first_allowed_pred(p, preds, allowed_preds)
    return x

def flatten_blocks(blocks, include_split_merge=True):
    block_list = [flatten_block(block, include_split_merge) for block in blocks]
    return set.union(*block_list) if len(block_list) > 0 else []

def flatten_block(block, include_split_merge=True):
    acts = flatten_block_acts(block)
    if include_split_merge:
        split = block['start']
        merge = block['end']
        if split:
            acts.update(split)
        if merge:
            acts.update(merge)
    return acts

def flatten_block_acts(block):
    return set({elem for item in block['activities'] for elem in (item if isinstance(item, tuple) else (item,))})

def latest_among(nodes, succ):
    return {n for n in nodes if not any(m in succ[n] for m in nodes if m != n)}

def earliest_among(nodes, succ):
    return {n for n in nodes if not any(n in succ[m] for m in nodes if m != n)}

def get_super_block_acts(super_block):
    acts = list(super_block["activities"])
    if super_block["start"]:
        acts.append(super_block["start"])
    if super_block["end"]:
        acts.append(super_block["end"])
    return acts