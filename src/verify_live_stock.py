"""Verify each selected article through its real WB product page, then freeze public evidence."""
import json
from pathlib import Path
from refresh_live import capture
from services.wb_live import install_capture
from shortlist_live import qualify

if __name__=='__main__':
    install_capture()
    path=Path('data/live/selected.json')
    rows=json.loads(path.read_text(encoding='utf8'))
    failures=[]
    for item in rows:
        nm=item['id']; cache=Path(f'data/live/verified_{nm}.json')
        try:
            result=json.loads(cache.read_text(encoding='utf8')) if cache.exists() else capture(f'https://www.wildberries.ru/catalog/{nm}/detail.aspx','/detail')
            p=next(p for p in result['products'] if p['id']==nm)
            cache.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
            if not qualify(p,item['category']):raise ValueError('Required stock/price no longer available')
            item['live']=p;item['checkedAt']=result['checkedAt'];item['verifiedDetail']=True
            path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
            print(nm,'verified',flush=True)
        except Exception as e:
            failures.append((nm,str(e)));print(nm,'FAILED',str(e),flush=True)
    if failures:raise RuntimeError(failures)
    print('All 70 articles verified on product pages',flush=True)
