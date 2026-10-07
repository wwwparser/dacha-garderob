import concurrent.futures
import json
import re
from pathlib import Path
from services.wb_service import StaticClient

OUT = Path('data/products')
OUT.mkdir(parents=True, exist_ok=True)
def candidates():
    found = {}
    for path in Path('data/search').glob('*.json'):
        stem = path.stem.replace('specific_', '')
        cat = next((c for c in ['boots','jackets','pants','hats','gloves'] if stem.startswith(c)), None)
        if cat is None:
            continue
        for row in json.loads(path.read_text(encoding='utf8'))['results']:
            m = re.search(r'/catalog/(\d+)/detail', row['url'])
            if m:
                nm = int(m[1])
                if nm < 1000000000:
                    found[nm] = {'id': nm, 'category': cat, 'serp': row}
    return list(found.values())

def collect(item):
    path = OUT / f"{item['id']}.json"
    if path.exists():
        return item['id'], 'cache'
    client = StaticClient(pause=.2, timeout=12, max_retries=2, backoff=3)
    try:
        card = client.basket_card(item['id'])
        feedback = client.feedbacks(card['imt_id'])
        item.update(card=card, feedback=feedback, checked='2026-10-07')
        path.write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf8')
        return item['id'], card.get('imt_name'), len(feedback.get('feedbacks',[]))
    except Exception as e:
        with Path('data/collection_errors.jsonl').open('a',encoding='utf8') as f:
            f.write(json.dumps({'id':item['id'],'error':str(e)},ensure_ascii=False)+'\n')
        return item['id'], str(e)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(5) as pool:
        for result in pool.map(collect,candidates()):
            print(result,flush=True)
