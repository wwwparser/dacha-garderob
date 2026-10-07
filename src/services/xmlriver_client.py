import os
import time
import xml.etree.ElementTree as ET
import requests


def search(query):
    user, key = os.getenv('XMLRIVER_USER'), os.getenv('XMLRIVER_KEY')
    if not user or not key:
        raise RuntimeError('Нужны XMLRIVER_USER и XMLRIVER_KEY в .env')
    for attempt in range(3):
        r = requests.get('https://xmlriver.com/search/xml', params={
            'user': user, 'key': key, 'query': query, 'country': 2643,
            'lr': 'ru', 'page': 1, 'groupby': 10}, timeout=120)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        error = root.find('.//error')
        if error is None:
            return [{'url': d.findtext('url'), 'title': ''.join(d.find('title').itertext()) if d.find('title') is not None else '',
                     'snippet': ' '.join(''.join(p.itertext()) for p in d.findall('.//passage'))}
                    for d in root.findall('.//doc')]
        message = ''.join(error.itertext())
        if any(w in message.lower() for w in ['баланс', 'средств', 'превышено']):
            raise RuntimeError(message)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(message)
