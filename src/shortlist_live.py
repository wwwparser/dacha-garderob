import json
import re
from pathlib import Path
from collections import Counter

CAPS={'boots':3000,'jackets':5000,'pants':3000,'hats':1000,'gloves':1000,'galoshes':1800,'clogs':1500}
TARGETS={'boots':[43,44,45],'galoshes':[43,44,45],'clogs':[43,44,45],'jackets':[54,56,58],'pants':[54,56,58]}

def coverage(size,category):
    text=str(size.get('origName') or size['name']) if category in ['jackets','pants'] else str(size['name'])
    if 'кг' in text.lower():return set()
    if category in ['jackets','pants'] and not re.match(r'^\d{2}',text):
        text=str(size['name'])
    # Stock labels can combine clothing size and height: 52-54/170-176, 54-182.
    text=re.split(r'[/_](?=\d{3})',text)[0]
    text=re.split(r'[-/](?=\d{3})',text)[0]
    if 'см' in text.lower() or re.search(r'\d[.,]\d',text):return set()
    nums=[int(n) for n in re.findall(r'(?<!\d)\d{2}(?!\d)',text)]
    if len(nums)==2 and nums[0]<=nums[1] and nums[1]-nums[0]<=8:
        return set(range(nums[0],nums[1]+1))
    return set(nums)

def offers(p,category):
    return [s for s in p.get('sizes',[]) if s.get('wh') and s.get('price',{}).get('product')]

def qualify(p,category):
    if p.get('totalQuantity')==0:return False
    ss=offers(p,category)
    if not ss:return False
    targets=TARGETS.get(category,[])
    if targets:
        for t in targets:
            found=[s for s in ss if t in coverage(s,category)]
            if not found or min(s['price']['product']/100 for s in found)>CAPS[category]:return False
    elif min(s['price']['product']/100 for s in ss)>CAPS[category]:return False
    return True

def candidates(category):
    result=[]
    for path in Path('data/live').glob(f'search_{category}*.json'):
        d=json.loads(path.read_text(encoding='utf8'))
        for p in d['products']:
            if qualify(p,category):result.append((p,d['checkedAt']))
    return result

if __name__=='__main__':
    for cat in CAPS:
        cand=candidates(cat)
        seen=set();distinct=[]
        for p,date in cand:
            if p['root'] not in seen:
                seen.add(p['root']);distinct.append((p,date))
        print('\n'+cat,'qualifying roots',len(distinct))
        for p,date in distinct[:16]:
            print(p['id'],p['brand'],p['name'],p.get('reviewRating'),p.get('feedbacks'),
                  [(s['name'],s.get('origName'),s['price']['product']/100) for s in offers(p,cat)][:9])
