def choose_first_fit_index(required_blocks, available_blocks, bypass_count=0, max_bypasses=2):
    if len(required_blocks) < 2:
        return None

    if bypass_count >= max_bypasses:
        return None

    if required_blocks[0] <= available_blocks:
        return None

    for index, blocks in enumerate(required_blocks[1:], start=1):
        if 0 < blocks <= available_blocks:
            return index

    return None
