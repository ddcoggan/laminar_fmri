import math
def seconds_to_text(secs):
    days = int(math.floor(secs//86400))
    hours = int(math.floor((secs - days*86400)//3600))
    minutes = int(math.floor((secs - days*86400 - hours*3600)//60))
    seconds = secs - days*86400 - hours*3600 - minutes*60
    result = ""
    if days:
        result += f"{days} day{'s' if days>1 else ''}, "
    if hours:
        result += f"{hours} hour{'s' if hours>1 else ''}, "
    if minutes:
        result += f"{minutes} minute{'s' if minutes>1 else ''}, "
    result += f"{seconds:.3f} seconds"
    return result

