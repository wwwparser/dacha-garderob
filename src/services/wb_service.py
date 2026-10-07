"""Direct Wildberries static cards and reviews, based on the installed WB skill."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.codex/skills/wildberries/scripts'))
from wb_client import WBClient, WBError, _safe_json


class StaticClient(WBClient):
    def basket_card(self, nm):
        short = nm // 100000
        guessed = int(self._basket_host(nm)) if short <= 5041 else 26 + (short - 5042) // 264
        hosts = [guessed] + [guessed + n for n in [-1, 1, -2, 2, -3, 3, -4, 4]]
        hosts += list(range(26, 90)) if short > 5041 else []
        for host in dict.fromkeys(hosts):
            if host < 1:
                continue
            url = f'https://basket-{host:02d}.wbbasket.ru/vol{short}/part{nm//1000}/{nm}/info/ru/card.json'
            try:
                r = self.session.get(url, timeout=5)
            except Exception:
                continue
            if r.status_code == 200:
                card = _safe_json(r.content)
                card['_basket_host'] = f'{host:02d}'
                card['_source'] = url
                return card
        raise WBError(f'No static card: {nm}')
