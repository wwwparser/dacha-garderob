import json
import sys
from pathlib import Path
from collections import Counter
for nm in map(int,sys.argv[1:]):
    d=json.loads(Path(f'data/products/{nm}.json').read_text(encoding='utf8'))
    f=d['feedback'].get('feedbacks') or []
    print(nm,Counter(x.get('nmId') for x in f))
    print(json.dumps(f[:1],ensure_ascii=False)[:1200])
