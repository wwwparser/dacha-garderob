import json
import re
from pathlib import Path
from collections import Counter
from PIL import Image

rows=json.loads(Path('data/catalog.json').read_text(encoding='utf8'))
assert len(rows)==50 and len({r['id'] for r in rows})==50
assert set(Counter(r['category'] for r in rows).values())=={10}
for cat in {r['category'] for r in rows}:
    assert sorted(r['rank'] for r in rows if r['category']==cat and r['rank'])==[1,2,3]
for p in rows:
    raw=json.loads(Path(f"data/products/{p['id']}.json").read_text(encoding='utf8'))
    assert not any(o['name']=='Пол' and o['value'] in ['Женский','Детский','Мальчики','Девочки'] for o in raw['card'].get('options',[])),p['id']
    assert p['quotes'],p['id']
    assert sum(len(q['text'].split()) for q in p['quotes'])<=25
    for quote in p['quotes']:
        assert quote['nm']==p['id']
        assert any(quote['text'].removesuffix('…') in re.sub(r'\s+',' ',' '.join(str(f.get(k) or '') for k in ['text','pros','cons'])).strip()
                   and f.get('nmId')==p['id'] and f.get('createdDate','')[:10]==quote['date'] and f.get('productValuation')==quote['stars']
                   for f in raw['feedback'].get('feedbacks') or []),(p['id'],quote)
    with Image.open(f"assets/products/{p['id']}.webp") as im:
        im.verify()
print('Data verified: 50 unique models, 10/category, 3 ranked/category, 50 valid images, all quotes match exact article and source.')

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765',wait_until='networkidle')
    assert page.locator('.card').count()==10
    for cat in ['boots','jackets','pants','hats','gloves']:
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
        page.keyboard.press('Escape')
        assert not page.locator('dialog').evaluate('(d)=>d.open')
    page.locator('#allView').click()
    page.locator('#search').fill('несуществующийтовар')
    assert page.locator('.card').count()==0 and page.locator('#empty').is_visible()
    page.locator('#search').fill('')
    page.locator('#sort').select_option('rating')
    assert page.locator('.card').count()==10
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
print('UI verified: five categories, top-3, images, reviews, Escape, empty search, sorting, desktop/mobile, no page errors.')
