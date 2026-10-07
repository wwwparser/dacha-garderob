import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from collect import collect
from shortlist_live import candidates,qualify,offers

PREFERRED={
 'boots':[494130501,837177587,187239443,96474254,200769526,825741529,827273130,548363565,41249522,41808753],
 'jackets':[16637617,14698790,44294948,502173334,50707400,256672233,866085062,195728127,312859512,1508558912],
 'pants':[781558458,264417827,317256307,173922079,166344517,585245983,173995958,123815724,137828433,48447460],
 'hats':[44966637,269650868,186774542,243023820,445326939,40477497,584725693,784124322,527481840,546206508],
 'gloves':[193420818,658381413,261052067,46227846,276579933,178147916,252973799,724887961,182205892,502200411],
 'galoshes':[622280060,138066938,256354333,72097387,534711518,490854957,649098870,173235342,218715143,523965926],
 'clogs':[224854106,213854380,589451435,262750716,893022646,806730007,984699032,421062996,907029896,768747558],
}

def pools(cat):
    found={p['id']:(p,date) for p,date in candidates(cat)}
    for path in list(Path('data/live').glob('card_[0-9]*.json'))+list(Path('data/live').glob('verified_[0-9]*.json')):
        d=json.loads(path.read_text(encoding='utf8'))
        for p in d['products']:
            if p['id'] in PREFERRED[cat] and qualify(p,cat):found[p['id']]=(p,d['checkedAt'])
    return found

if __name__=='__main__':
    selected=[];seen_roots=set()
    for cat,preferred in PREFERRED.items():
        pool=pools(cat)
        fallback=sorted(pool,key=lambda nm:(pool[nm][0].get('feedbacks',0)<30,pool[nm][0]['id']>1000000000,-(pool[nm][0].get('reviewRating') or 0)))
        chosen=[]
        for nm in list(dict.fromkeys(preferred+fallback)):
            if nm not in pool:continue
            p,date=pool[nm]
            if p['root'] in seen_roots or (nm>1000000000 and nm not in preferred):continue
            if cat=='jackets' and not any(k in p['name'].lower() for k in ['куртка','бушлат']):continue
            if 'женск' in p['name'].lower() or 'детск' in p['name'].lower():continue
            chosen.append({'id':nm,'category':cat,'checkedAt':date,'live':p,'serp':{}})
            seen_roots.add(p['root'])
            if len(chosen)==10:break
        print(cat,len(chosen),[(r['id'],r['live']['name']) for r in chosen],flush=True)
        if len(chosen)<10:raise RuntimeError('Need more qualifying live candidates: '+cat)
        selected+=chosen
    Path('data/live/selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf8')
    with ThreadPoolExecutor(5) as pool:
        for result in pool.map(collect,selected):print(result,flush=True)
