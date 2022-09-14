def first_index(needles, haystack):
    result = None
    for needle in needles:
        idx = haystack.find(needle)
        if idx != -1:
            if result is None:
                result = idx
            else:
                result = min(result, idx)
    return result

def last_index(needles, haystack):
    result = None
    for needle in needles:
        idx = haystack.rfind(needle)
        if idx != -1:
            if result is None:
                result = idx
            else:
                result = max(result, idx)
    return result

def remove_common_prefixes(strings):
    if len(strings) == 1:
        return strings
    def split(s):
        i = first_index(r'[ _/\\+~*#.,-]', s)
        if i:
            return s[:i+1], s[i+1:]
        else:
            return '', s
    while True:
        split_strs = [split(l) for l in strings]
        if any([True if s[0]=='' else False for s in split_strs]):
            break # at least one has no prefix
        prefixes = set([p for (p,_) in split_strs])
        if len(prefixes) != 1:
            break # no common prefix
        strings = [s[1] for s in split_strs] # remove prefix
    return strings


def remove_common_suffixes(strings):
    if len(strings) == 1:
        return strings
    def split(s):
        i = last_index(r'[ _/\\+~*#.,-]', s)
        if i:
            return s[:i], s[i:]
        else:
            return s, ''
    while True:
        split_strs = [split(l) for l in strings]
        if any([True if s[1]=='' else False for s in split_strs]):
            break # at least one has no suffix
        prefixes = set([s for (_,s) in split_strs])
        if len(prefixes) != 1:
            break # no common suffix
        strings = [s[0] for s in split_strs] # remove suffix
    return strings


def remove_common_prefixes_and_suffixes(strings):
    return remove_common_prefixes(remove_common_suffixes(strings))
