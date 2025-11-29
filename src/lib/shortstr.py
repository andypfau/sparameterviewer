import re
import itertools
import logging



def shorten_string_list(strings: list[str], elide_str: str = '…', target_len: int = 25) -> list[str]:
    """
    Shorten a list of strings, such that all strings are still distinct (at least if they were distinct before).

    strings:    list of strings to shorten
    elide_str:  the string to use to indicate elision
    target_len: target maximum length of each string (no elisions are attempted if the strings are already this short)
    """

    assert len(elide_str) == 1
    if len(strings) < 1:
        return []

    TARGET_ELIDED_LEN = 3  # e.g. 3 means to elide "LongString" to e.g. "Lo…"
    MAX_TOKENS_TO_TRY = 1_000  # empirical safeguard against the algorithm running slow

    def ntuple_strings(list_of_tokens: list[str], n: int) -> list[str]:
        """ e.g. ntuple_strings(['a','b','c','d'],3) -> ['abc','bcd'] """
        if len(list_of_tokens) < n:
            return [''.join(list_of_tokens)]
        return [''.join(list_of_tokens[i:i+n]) for i in range(len(list_of_tokens)-n+1)]
        
    def split_into_tokens(s: str) -> list[str]:
        """ e.g. split_into_tokens('The File.s2p') -> ['The', ' ', 'File', '.', 's2p'] """
        return [p for p in re.split(r'([ _/\\+~*#.,;-]|\b)',s) if p != '']

    def elide(string: str, elidable_string: str, elision_string: str, final_len: int) -> str:
        """ e.g. elide('HelloWorld~', 'World', '~', 3) -> 'HelloWo~' """
        len_elidable, len_elision = len(elidable_string), len(elision_string)
        assert len_elidable >= final_len and len_elision == 1
        replacement = elidable_string[0:final_len-len_elision] + elision_string
        return string.replace(elidable_string,replacement).replace(elision_string+elision_string,elision_string)

    def target_reached(strings: list[str]) -> bool:
        return max([len(string) for string in strings]) < target_len
    
    if target_reached(strings):
        return strings

    # how many distinct strings do we have? Note that it could be that a few of them are already idential, so our goal is that no
    #   matter what we do, the number of distinct strings does not get lower
    original_distinct_strings = len(set(strings))

    strings_tokens = [split_into_tokens(s) for s in strings]
    ntuple_max = max([len(tokens) for tokens in strings_tokens])

    impacts = []
    for tuple_size in range(1, ntuple_max+1):

        # create a set of substrings that occur in the strings
        strings_tokens_tuples = [ntuple_strings(tokens,tuple_size) for tokens in strings_tokens]
        elidable_strings = set([t for t in itertools.chain(*strings_tokens_tuples)])

        for elidable_string in elidable_strings:
            if len(elidable_string) <= TARGET_ELIDED_LEN:
                continue  # makes no sense to elide such a short string
            
            # calculate how much shorter the overall list of string would become with this elision
            n = sum([1 if elidable_string in string else 0 for string in strings])
            impact = (n**2) * max(2, len(elidable_string) - TARGET_ELIDED_LEN)  # empirical
            impacts.append((impact, elidable_string))
            
            if len(impacts) > MAX_TOKENS_TO_TRY:
                break
        if len(impacts) > MAX_TOKENS_TO_TRY:
            break

    impacts = list(sorted(impacts, key=lambda t: t[0], reverse=True))
    # impacts now is a list of (impact,elidable_string) tuples, sorted such that the element with the highest impact comes first
    
    for i,(_,elidable_string) in enumerate(impacts):
        
        new_strings = [elide(s,elidable_string,elide_str,TARGET_ELIDED_LEN) for s in strings]
        
        new_distinct_strings = len(set(new_strings))
        if new_distinct_strings == original_distinct_strings:
            strings = new_strings
            
            if target_reached(strings):
                break

        if i >= MAX_TOKENS_TO_TRY:
            break
    
    return strings
