import os


def get_unique_short_filenames(names: "list[str]", min_length: int = 5) -> "list[str]":
    
    def is_unique(all: "list[str]", full: str, short: str) -> bool:
        for other in all:
            if full==other:
                continue
            if short in other:
                return False
        return True
    
    result = []
    for name_full in names:
        name = name_full
            
        # try to remove extension
        fn,_ = os.path.splitext(name)
        if is_unique(names, name_full, fn):
            name = fn

        if len(name) <= 10:
            # just use full name
            result.append(name)
            continue
        
        # crop off as much as possible at the end
        excess_end = 0
        for i in range(len(name)):
            short = name[:-1-i]
            if is_unique(names, name_full, short):
                excess_end = i
            else:
                break
        if excess_end > 3:
            excess_end = min(excess_end-3, len(name)-8)
            #print(f'{name}: cropping off {excess_end} at end')
            name = name[:-excess_end]

        # crop off as much as possible at the beginning
        excess_start = 0
        for i in range(len(name)):
            short = name[i:]
            if is_unique(names, name_full, short):
                excess_start = i
            else:
                break
        if excess_start > 3:
            excess_start = min(excess_start-3, len(name)-8)
            #print(f'{name}: cropping off {excess_start} at start')
            name = name[excess_start:]
        
        result.append(name)

    return result


