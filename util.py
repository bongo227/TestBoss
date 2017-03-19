def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index( last, start )

        matches = [s[start:end]]
        
        # Check for other matches recursivly
        after = find_between(s[end:], first, last)
        if after:
            matches.extend(after)

        return matches
    
    except ValueError:
        return None