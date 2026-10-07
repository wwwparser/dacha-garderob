"""Publish only detail-verified live offers, with manually authored editorial notes."""
import json,re,concurrent.futures
from pathlib import Path
from build_catalog import text_of,short_quote,get_image,SOURCES
from live_notes import NOTES,RANKS,REASONS
from shortlist_live import offers,coverage,TARGETS,qualify

def assemble(item):
    nm,cat,p=item['id'],item['category'],item['live']
    assert item.get('verifiedDetail') and qualify(p,cat),nm
    raw=json.loads(Path(f'data/products/{nm}.json').read_text(encoding='utf8'))
    c,f=raw['card'],raw['feedback'];use,pro,con,summary=NOTES[nm]
    reviews=[r for r in f.get('feedbacks') or [] if r.get('nmId')==nm and len(text_of(r).split())>=2]
    clean=[r for r in reviews if not re.search(r'\*\*|чечен|запинали|бронижил|хрена|хуй|пизд|ебан|деньги|списали',text_of(r),re.I)]
    pos=next((r for r in clean if (r.get('productValuation') or 0)>=4),None)
    neg=next((r for r in sorted(clean,key=lambda r:r.get('productValuation') or 5) if (r.get('productValuation') or 5)<=3 and r is not pos),None)
    qs=[short_quote(r) for r in [pos,neg] if r]
    if not qs and clean:qs=[short_quote(clean[0])]
    ss=offers(p,cat);targets=TARGETS.get(cat,[])
    if targets:ss=[s for s in ss if coverage(s,cat)&set(targets)]
    size_offers=[dict(ru=s['name'],manufacturer=s.get('origName') or s['name'],price=s['price']['product']/100,
        covers=sorted(coverage(s,cat)&set(targets))) for s in ss]
    specs={o['name']:o['value'] for o in c.get('options',[]) if o['name'] in ['Сезон','Состав','Пол','Материал подкладки','Утеплитель','Вид застежки','Плотность синтетического утеплителя','Материал изделия','Комплектация'] and len(str(o['value']))<180}
    if not specs:specs={'Описание продавца':re.sub(r'\s+',' ',c.get('description',''))[:240]}
    rank=RANKS[cat].index(nm)+1 if nm in RANKS[cat] else None
    return dict(id=nm,category=cat,name=c['imt_name'],brand=p.get('brand') or 'Без бренда',use=use,
        pros=[pro],cons=[con],reviewSummary=summary,rank=rank,reason=REASONS.get(nm),
        rating=p.get('reviewRating'),count=p.get('feedbacks') or 0,quotes=qs,specs=specs,
        cardSource=c['_source'],reviewSource=f"https://feedbacks2.wb.ru/feedbacks/v1/{c['imt_id']}",imt=c['imt_id'],
        exactTextReviews=len(reviews),imageSource=f"https://basket-{c['_basket_host']}.wbbasket.ru/vol{nm//100000}/part{nm//1000}/{nm}/images/big/1.webp",
        price=min(s['price'] for s in size_offers),priceMax=max(s['price'] for s in size_offers),
        sizeOffers=size_offers,requiredSizes=targets,checkedAt=item['checkedAt'],verifiedDetail=True)

if __name__=='__main__':
    rows=[assemble(x) for x in json.loads(Path('data/live/selected.json').read_text(encoding='utf8'))]
    with concurrent.futures.ThreadPoolExecutor(5) as pool:list(pool.map(get_image,rows))
    Path('catalog.js').write_text('const CATALOG = '+json.dumps(rows,ensure_ascii=False,indent=2)+';\nconst SOURCES = '+json.dumps(SOURCES,ensure_ascii=False,indent=2)+';\n',encoding='utf8')
    Path('data/catalog.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    print('Built',len(rows),'models;',sum(bool(r['quotes']) for r in rows),'with exact article quotes')
