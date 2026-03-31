def compute_diff(old: dict, new: dict):
    diff = {}
    keys = set(old.keys()).union(new.keys())

    for k in keys:
        if old.get(k) != new.get(k):
            diff[k] = {
                "before": old.get(k),
                "after": new.get(k)
            }

    return diff