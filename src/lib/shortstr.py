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

    DEFAULT_ELIDED_LEN = 3
    MAX_TUPLE_SIZE = 25  # higher numbers -> more powerful, but also slower...

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
    ntuple_max = min(max([len(tokens) for tokens in strings_tokens]), MAX_TUPLE_SIZE)

    impacts = []
    for tuple_size in range(ntuple_max, 0, -1):

        # create a set of substrings that occur in the strings
        strings_tokens_tuples = [ntuple_strings(tokens,tuple_size) for tokens in strings_tokens]
        elidable_strings = set([t for t in itertools.chain(*strings_tokens_tuples)])

        for elidable_string in elidable_strings:
            if len(elidable_string) <= DEFAULT_ELIDED_LEN:
                continue  # makes no sense to elide such a short string
            
            # calculate how much shorter the overall list of string would become with this elision
            n = sum([1 if elidable_string in string else 0 for string in strings])
            impact = n * max(2, len(elidable_string) - DEFAULT_ELIDED_LEN)
            impacts.append((impact, elidable_string))

    # impacts now is a list (impact,elidable_string), where the elidable string with the most impact comes first
    impacts = list(sorted(impacts, key=lambda t: t[0], reverse=True))
    
    for _,elidable_string in impacts:
        
        new_strings = [elide(s,elidable_string,elide_str,DEFAULT_ELIDED_LEN) for s in strings]
        
        new_distinct_strings = len(set(new_strings))
        if new_distinct_strings == original_distinct_strings:
            strings = new_strings
            
            if target_reached(strings):
                return strings

    return strings
