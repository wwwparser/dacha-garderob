import concurrent.futures
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from services.xmlriver_client import search

load_dotenv()
OUT = Path('data/search')
OUT.mkdir(parents=True, exist_ok=True)
queries = {
    'boots1': 'site:wildberries.ru/catalog/ сапоги ЭВА мужские утепленные Nordman Torvi отзывы',
    'boots2': 'site:wildberries.ru/catalog/ сапоги мужские утепленные Вездеход Дюна Lemigo',
    'boots3': 'site:wildberries.ru/catalog/ сапоги резиновые мужские утепленные Демар',
    'jackets1': 'site:wildberries.ru/catalog/ куртка рабочая утепленная мужская отзывы',
    'jackets2': 'site:wildberries.ru/catalog/ куртка мужская демисезонная софтшелл флис отзывы',
    'pants1': 'site:wildberries.ru/catalog/ брюки рабочие утепленные мужские отзывы',
    'pants2': 'site:wildberries.ru/catalog/ брюки мужские флис утепленные софтшелл отзывы',
    'hats1': 'site:wildberries.ru/catalog/ шапка мужская флисовая утепленная отзывы',
    'hats2': 'site:wildberries.ru/catalog/ шапка ушанка мужская зимняя отзывы',
    'gloves1': 'site:wildberries.ru/catalog/ перчатки рабочие утепленные латекс зимние отзывы',
    'gloves2': 'site:wildberries.ru/catalog/ перчатки мужские зимние флис софтшелл отзывы',
    'advice1': 'сапоги ЭВА для дачи осенью зимой недостатки Nordman Torvi отзывы',
    'advice2': 'одежда для работы на даче осенью зимой флис рабочая куртка выбор',
    'advice3': 'перчатки для работы зимой сад влажные утепленные латекс выбор',
}

def one(pair):
    name, query = pair
    path = OUT / f'{name}.json'
    if path.exists():
        return name, len(json.loads(path.read_text(encoding='utf8'))['results'])
    try:
        rows = search(query)
        path.write_text(json.dumps({'query': query, 'results': rows}, ensure_ascii=False, indent=2), encoding='utf8')
        return name, len(rows)
    except Exception as e:
        return name, str(e)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(one, queries.items()):
            print(result, flush=True)
