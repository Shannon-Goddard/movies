import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
with open(os.path.join('data','index.json'), encoding='utf-8') as f:
    data = json.load(f)
sample = data[0]
for k, v in sample.items():
    print(f'{k}: {len(str(v))} chars  |  {str(v)[:60]}')
