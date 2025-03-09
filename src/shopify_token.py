from selenium import webdriver
import json
import os
import re


class ShopifyTokenManager:
    def __init__(self, store_url: str, cache_file: str = 'data/tokens/shopify_tokens.json'):
        self.store_url = store_url
        self.cache_file = cache_file
        self.tokens = self._load_cached_tokens()

    def _load_cached_tokens(self) -> dict:
        if not os.path.exists(self.cache_file):
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_cached_tokens(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.tokens, f, indent=2)

    def get_token(self, force_refresh: bool = False) -> str:
        if not force_refresh and self.store_url in self.tokens:
            return self.tokens[self.store_url]['token']

        token = self._fetch_new_token()
        self.tokens[self.store_url] = {'token': token}
        self._save_cached_tokens()
        return token

    def _fetch_new_token(self) -> str:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        driver = webdriver.Chrome(options=options)
        try:
            driver.get(f'https://{self.store_url}')

            logs = driver.get_log('performance')

            token = None
            for log in logs:
                log_data = json.loads(log['message'])['message']

                if 'Network.requestWillBeSent' in log_data.get('method', ''):
                    request = log_data.get('params', {}).get('request', {})
                    headers = request.get('headers', {})

                    if 'x-shopify-storefront-access-token' in headers:
                        token = headers['x-shopify-storefront-access-token']
                        break

            if not token:
                page_source = driver.page_source
                token_match = re.search(
                    r'x-shopify-storefront-access-token["\']:\s*["\']([^"\']+)["\']', page_source)
                if token_match:
                    token = token_match.group(1)

            if not token:
                raise Exception("Could not extract Storefront API token")
            return token

        finally:
            driver.quit()
