import json
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote
from services.wb_live import install_capture,navigate,responses,evaluate

ROOT=Path('data/live');ROOT.mkdir(parents=True,exist_ok=True)
QUERIES={
 'boots':'сапоги эва мужские утепленные',
 'jackets':'куртка рабочая мужская зимняя утепленная',
 'pants':'брюки рабочие мужские утепленные',
 'hats':'шапка мужская флисовая зимняя',
 'gloves':'перчатки рабочие утепленные зимние',
 'galoshes':'галоши мужские утепленные',
 'clogs':'сабо мужские утепленные без пятки',
}

def capture(url,kind):
    navigate(url)
    for _ in range(20):
        time.sleep(1)
        rows=responses()
        for r in rows:
            if kind in r['url']:
                products=r['data'].get('products') or []
                if products:
                    return {'checkedAt':datetime.now(timezone.utc).isoformat(), 'source':'WB live browser', 'products':products}
    raise RuntimeError('WB page did not return product data')

if __name__=='__main__':
    install_capture()
    # Live searches contain only size offers returned by WB for the current destination.
    for category,query in QUERIES.items():
        path=ROOT/f'search_{category}.json'
        if path.exists():continue
        result=capture('https://www.wildberries.ru/catalog/0/search.aspx?search='+quote(query),'/search')
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        print(category,len(result['products']),flush=True)
