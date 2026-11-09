def choose_bypass_index(required_blocks, available_blocks, bypass_count=0, max_bypasses=2):
    if len(required_blocks) < 2:
        return None

    if bypass_count >= max_bypasses:
        return None

    if required_blocks[0] <= available_blocks:
        return None

    candidates = [
        (blocks, index)
        for index, blocks in enumerate(required_blocks[1:], start=1)
        if 0 < blocks <= available_blocks
    ]

    if not candidates:
        return None

    return min(candidates)[1]
