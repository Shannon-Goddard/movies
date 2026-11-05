import json

d = json.load(open('data/index.json', encoding='utf-8'))

def keep(x):
    s = x.get('duration_sec', 0)
    if not s: return True
    t = x.get('type', '')
    if t == 'short': return s >= 180
    if t == 'cartoon': return s >= 300
    return s >= 600

out = [x for x in d if keep(x)]
json.dump(out, open('data/index.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(f'Before: {len(d)}  After: {len(out)}  Removed: {len(d)-len(out)}')
