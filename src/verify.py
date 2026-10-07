import json
import re
from pathlib import Path
from collections import Counter
from PIL import Image

rows=json.loads(Path('data/catalog.json').read_text(encoding='utf8'))
assert len(rows)==70 and len({r['id'] for r in rows})==70
assert set(Counter(r['category'] for r in rows).values())=={10}
for cat in {r['category'] for r in rows}:
    assert sorted(r['rank'] for r in rows if r['category']==cat and r['rank'])==[1,2,3]
for p in rows:
    raw=json.loads(Path(f"data/products/{p['id']}.json").read_text(encoding='utf8'))
    assert not any(o['name']=='Пол' and o['value'] in ['Женский','Детский','Мальчики','Девочки'] for o in raw['card'].get('options',[])),p['id']
    assert p['verifiedDetail'] and p['price']>0 and p['sizeOffers'],p['id']
    live=json.loads(Path(f"data/live/verified_{p['id']}.json").read_text(encoding='utf8'))
    product=next(r for r in live['products'] if r['id']==p['id'])
    from shortlist_live import qualify,coverage,offers
    assert qualify(product,p['category']),p['id']
    covered=set().union(*(set(s['covers']) for s in p['sizeOffers']))
    assert covered==set(p['requiredSizes']),p['id']
    assert p['checkedAt']==live['checkedAt']
    for s in p['sizeOffers']:
        assert any(s['ru']==r['name'] and s['manufacturer']==r.get('origName',r['name']) and s['price']==r['price']['product']/100 for r in offers(product,p['category'])),(p['id'],s)
    if p['rank']:assert p['quotes'],p['id']
    assert sum(len(q['text'].split()) for q in p['quotes'])<=25
    for quote in p['quotes']:
        assert quote['nm']==p['id']
        assert any(quote['text'].removesuffix('…') in re.sub(r'\s+',' ',' '.join(str(f.get(k) or '') for k in ['text','pros','cons'])).strip()
                   and f.get('nmId')==p['id'] and f.get('createdDate','')[:10]==quote['date'] and f.get('productValuation')==quote['stars']
                   for f in raw['feedback'].get('feedbacks') or []),(p['id'],quote)
    with Image.open(f"assets/products/{p['id']}.webp") as im:
        im.verify()
print('Data verified: 70 unique models, 10/category, 3 ranked/category, all live offers cover requested sizes, images and exact-article quotes valid.')

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765',wait_until='networkidle')
    assert page.locator('.card').count()==10
    for cat in ['boots','jackets','pants','hats','gloves','galoshes','clogs']:
        page.locator(f'[data-category="{cat}"]').click()
        page.locator('#allView').click()
        assert page.locator('.card').count()==10
        for img in page.locator('.card img').all():
            img.scroll_into_view_if_needed()
            img.evaluate('(i)=>i.loading="eager"')
        page.wait_for_function('Array.from(document.querySelectorAll(".card img")).every(i=>i.complete&&i.naturalWidth>0)')
        assert page.locator('.card img').evaluate_all('(imgs)=>imgs.every(i=>i.complete&&i.naturalWidth>0)')
        page.locator('#topView').click()
        assert page.locator('.card').count()==3
        page.locator('[data-detail]').first.click()
        assert page.locator('dialog').evaluate('(d)=>d.open')
        assert page.locator('.quote').count()>=1
        assert page.locator('.offer-list>div').count()>=1
        page.keyboard.press('Escape')
        assert not page.locator('dialog').evaluate('(d)=>d.open')
    page.locator('#allView').click()
    page.locator('#search').fill('несуществующийтовар')
    assert page.locator('.card').count()==0 and page.locator('#empty').is_visible()
    page.locator('#search').fill('')
    page.locator('#sort').select_option('rating')
    assert page.locator('.card').count()==10
    page.locator('#sort').select_option('price')
    prices=page.locator('.budget>b').all_text_contents()
    values=[float(re.sub(r'[^\d,]','',p).replace(',','.')) for p in prices]
    assert values==sorted(values)
    page.locator('[data-category="boots"]').click()
    page.locator('#sort').select_option('pick')
    page.evaluate('scrollTo(0,0)')
    page.screenshot(path='data/desktop.png',full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path='data/mobile.png',full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Mobile overflow'
    page.locator('[data-detail]').first.click()
    assert page.locator('.quote').count()>0
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='data/mobile-modal.png')
    page.locator('.close').click()
    assert not errors,errors
    browser.close()
print('UI verified: seven categories, top-3, live sizes, images, reviews, modal, search, sorting, desktop/mobile, no page errors.')
