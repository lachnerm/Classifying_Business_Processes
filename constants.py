class_score_thresholds = {
        "unstructured": -0.4,
        "looselyStructured": 0.25,
        "semiStructured": 0.75
}

REFINEMENT_SCORES_SB_TO_SB = {
    # Augur
    (">d", "<=>"):  +0.50,  # direct ordered co‑occurrence
    #("<d", "<=>"):  +0.50,  # direct ordered co‑occurrence

    # Don't occur
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
    ("<",  "-"):    +0.05,  # before


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

