from statistics import median

def bootstrap_score(fn, ticket, n:int=80):
    vals=[fn() for _ in range(max(10,n))];
    return median(vals) if len(vals)>2 else (sum(vals)/len(vals))
