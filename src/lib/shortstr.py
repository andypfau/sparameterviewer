import re



def shorten_string_list(strings: list[str], elide_str: str = '…') -> list[str]:
    
    if len(strings) <= 1:
        return strings
        
    n = len(strings)
    tokens_list = [[p for p in re.split(r'([ _/\\+~*#.,;-]|\b)',s) if p != ''] for s in strings]
    max_len = max(*[len(l) for l in tokens_list])

    def shorten_in_direction(direction: int):
        assert direction in [-1, +1], f'Expected direction to be +1 or -1, got {direction}'
        
        pointers = [0 if direction==+1 else len(tokens_list[i]) for i in range(n)]
    
        def create_dictionary():
            dictionary = {}
            for i in range(n):
                if pointers[i] < 0 or pointers[i] >= len(tokens_list[i]):
                    continue
                token = tokens_list[i][pointers[i]]
                if isinstance(token, tuple):
                    continue
                indices = dictionary.get(token, list())
                indices.append(i)
                dictionary[token] = indices
            #print(f'Found {dictionary}')
            return dictionary

        def get_most_frequent_token(dictionary):
            if len(dictionary) < 1:
                return None
            
            elide_token, elide_token_count = None, 0
            for token,indices in dictionary.items():
                if isinstance(token, tuple):
                    continue
                count = len(dictionary[token])
                if count >= 2 and count > elide_token_count:
                    elide_token_count = count
                    elide_token = token
            return elide_token
    
        def try_shorten():
            dictionary = create_dictionary()
            if len(dictionary) == 1:
                #print(f'Perfect result{dictionary}; eliding, advancing')
                for i in range(n):
                    pointer = pointers[i]
                    if pointer < 0 or pointer >= len(tokens_list[i]):
                        continue
                    if not isinstance(tokens_list[i][pointer], tuple):
                        tokens_list[i][pointer] = (tokens_list[i][pointer],)
                    pointers[i] += direction
            else:
                #print(f'Ambiguous result {dictionary}')
                
                elide_token = get_most_frequent_token(dictionary)
                if elide_token is None:
                    #print('Nothing I can do, moving pointers, ending...')
                    for i in range(n):
                        pointers[i] += direction
                    return

                #print(f'Seeing what I can do with "{elide_token}"')
                for token,indices in dictionary.items():
                    if token == elide_token:
                        continue
                    for i in indices:
                        for offset in range(-2, +3+1):
                            pointer = pointers[i] + offset
                            if pointer < 0 or pointer >= len(tokens_list[i]):
                                continue
                            if tokens_list[i][pointer] == elide_token:
                                #print(f'Found token "{elide_token}" also in {tokens_list[i]} at {pointers[i]}+{offset}')
                                pointers[i] = pointer
                                break
                dictionary = create_dictionary()
                #print(f'Dictionary is now "dictionary"')
                if len(dictionary) == 1:
                    #print(f'Eliding "{elide_token}", advancing ...')
                    for token,indices in dictionary.items():
                        if token == elide_token:
                            for i in indices:
                                if not isinstance(tokens_list[i][pointers[i]], tuple):
                                    tokens_list[i][pointers[i]] = (tokens_list[i][pointers[i]],)
                                #pointers[i] += direction
                    for i in range(n):
                        pointers[i] += direction
                else:
                    #print('Nothing I can do, moving pointers, ending...')
                    for i in range(n):
                        pointers[i] += direction
                    return
    
        for _ in range(max_len):
            try_shorten()

    # run the algorithm twice; once forward, once backward
    shorten_in_direction(+1)
    shorten_in_direction(-1)
    
    def tokens_to_str(tokens):
        result = ''
        accu_str = ''
        accu_elide = ''
        
        def flush_accu(is_last=False):
            nonlocal result, accu_str, accu_elide
            is_first = result==''
            if accu_str != '':
                result += accu_str
                accu_str = ''
            if accu_elide != '':
                if len(accu_elide) >= 2:
                    if not (is_first or is_last):
                        result += elide_str
                else:
                    result += accu_elide
                accu_elide = ''
        
        for token in tokens:
            if isinstance(token, tuple):
                if accu_str:
                    flush_accu()
                accu_elide += token[0]
            else:
                if accu_elide:
                    flush_accu()
                accu_str += token
        flush_accu(is_last=True)
        
        return result
    
    return [tokens_to_str(tokens) for tokens in tokens_list]
