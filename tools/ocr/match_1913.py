"""Match the sections of the Companies Ordinance, 1984 to those of the Indian Companies Act, 1913 by title and wording
(TF-IDF cosine, then a monotone alignment, then strong out-of-order matches). Not a published table: every pair is a lead to confirm.
usage: python3 tools/ocr/match_1913.py <out.json>"""
import json, re, math, collections, sys
def secs(i):
    d = json.load(open(f'data/acts/{i}.json')); return [(s['no'], s['title'], ' '.join(s['text'])) for p in d['parts'] for s in p['sections']]
O = secs('companies-ordinance-1984'); A = secs('companies-act-1913')
stop = set("the of and or to in a an by for be is shall any such as it its under this that which with from on at are was not if may all other than has have been his her their he she they them but so no".split())
toks = lambda s: [w for w in re.findall(r'[a-z]{3,}', s.lower()) if w not in stop]
dO = [toks(t + ' ' + t + ' ' + x) for n, t, x in O]; dA = [toks(t + ' ' + t + ' ' + x) for n, t, x in A]
df = collections.Counter(w for d in dO + dA for w in set(d)); N = len(dO) + len(dA)
idf = {w: math.log(N / (1 + c)) + 1 for w, c in df.items()}
def vec(d):
    c = collections.Counter(d); v = {w: (1 + math.log(k)) * idf[w] for w, k in c.items()}; nr = math.sqrt(sum(x * x for x in v.values())) or 1
    return {w: x / nr for w, x in v.items()}
cos = lambda a, b: sum(x * b.get(w, 0) for w, x in (a.items() if len(a) <= len(b) else b.items())) if len(a) <= len(b) else sum(x * a.get(w, 0) for w, x in b.items())
VO = [vec(d) for d in dO]; VA = [vec(d) for d in dA]
TO = [vec(toks(t)) for n, t, x in O]; TA = [vec(toks(t)) for n, t, x in A]
S = [[0.6 * cos(VO[i], VA[j]) + 0.4 * cos(TO[i], TA[j]) for j in range(len(A))] for i in range(len(O))]
n, m, TH = len(O), len(A), 0.30
dp = [[0.0] * (m + 1) for _ in range(n + 1)]; back = [[None] * (m + 1) for _ in range(n + 1)]
for i in range(1, n + 1):
    for j in range(1, m + 1):
        v, b = dp[i - 1][j], ('skip',)
        s = S[i - 1][j - 1]
        if s >= TH and dp[i - 1][j - 1] + s > v: v, b = dp[i - 1][j - 1] + s, ('match', j - 1)
        if dp[i][j - 1] > v: v, b = dp[i][j - 1], ('left',)
        dp[i][j], back[i][j] = v, b
pairs = {}; i, j = n, m
while i > 0 and j > 0:
    b = back[i][j]
    if b[0] == 'left': j -= 1
    elif b[0] == 'skip': i -= 1
    else: pairs[i - 1] = b[1]; i -= 1; j = b[1]
for i in range(n):                                   # strong matches the alignment could not take (different order, or several sections to one)
    if i not in pairs:
        j = max(range(m), key=lambda k: S[i][k])
        if S[i][j] >= 0.55: pairs[i] = j
out = [{"a": O[i][0], "o": [A[j][0]], "score": round(S[i][j], 2)} for i, j in sorted(pairs.items())]
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(len(out), 'of', n, 'matched;', sum(1 for p in out if p['score'] >= 0.7), 'strong (>=0.7)')
