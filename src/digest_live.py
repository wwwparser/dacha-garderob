import json
import sys
from pathlib import Path
from build_catalog import text_of
selected=json.loads(Path('data/live/selected.json').read_text(encoding='utf8'))
for item in selected:
    if len(sys.argv)>1 and item['category']!=sys.argv[1]:continue
    nm=item['id'];d=json.loads(Path(f'data/products/{nm}.json').read_text(encoding='utf8'))
    c,f=d['card'],d['feedback']
    rows=[r for r in f.get('feedbacks') or [] if r.get('nmId')==nm and len(text_of(r).split())>2]
    print('\n',item['category'],nm,c['imt_name'], 'TEXT REVIEWS',len(rows))
    print('SPEC', {o['name']:o['value'] for o in c.get('options',[]) if o['name'] in ['Пол','Состав','Утеплитель','Материал подкладки','Материал изделия','Комплектация','Сезон']})
    print('DESCRIPTION',c.get('description','')[:240])
    for r in sorted(rows,key=lambda x:x.get('productValuation') or 5)[:1]+[r for r in rows if r.get('productValuation')==5][:1]:
        print(r.get('productValuation'),text_of(r)[:250])
