import time
import requests
from typing import Union, List
from src.models.product import Product
from src.models.base_scrapper import BaseScrapper
from selenium import webdriver


class WoolworthScrapper(BaseScrapper):
    def __init__(self) -> None:
        super().__init__()
        self.base_url = 'https://www.woolworths.com.au/apis/ui/Search/products'
        self.cookies = None
        self.last_cookie_refresh = 0
        self.cookie_expiry = 3600

    def _get_headers(self) -> dict:
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.woolworths.com.au',
            'priority': 'u=1, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.current_user_agent
        }

    def _set_cookies(self, force_refresh: bool = False) -> dict:
        current_time = time.time()
        if not force_refresh and self.cookies and (current_time - self.last_cookie_refresh) < self.cookie_expiry:
            return self.cookies

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-dev-shm-usage')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = webdriver.Chrome(options=options)
        try:
            driver.get('https://www.woolworths.com.au')
            cookies = driver.get_cookies()
            self.cookies = {cookie['name']: cookie['value']
                            for cookie in cookies}
            self.last_cookie_refresh = current_time
            return self.cookies
        except Exception as e:
            print(f"Error getting cookies: {e}")
            return {}
        finally:
            driver.quit()

    def _get_payload(self, search_term: str, page_number: int = 1, page_size: int = 5) -> dict:
        return {
            "Filters": [],
            "IsSpecial": False,
            "Location": f"/shop/search/products?searchTerm={search_term}",
            "PageNumber": page_number,
            "PageSize": page_size,
            "SearchTerm": search_term,
            "SortType": "TraderRelevance",
            "IsRegisteredRewardCardPromotion": None,
            "ExcludeSearchTypes": ["UntraceableVendors"],
            "GpBoost": 0,
            "GroupEdmVariants": True,
            "EnableAdReRanking": False,
            "flags": {
                "EnableProductBoostExperiment": False
            }
        }

    def _parse_response(self, results: dict, exact_name: str = None) -> Union[List[Product], None]:
        try:
            products = []
            if results['Products'] is None or results['SuggestedTerm'] is not None:
                return None
            for product_group in results['Products']:
                product_list = product_group.get('Products', [product_group])
                for product in product_list:
                    name = product.get('DisplayName', '')
                    if exact_name and name != exact_name:
                        continue
                    sku = str(product.get('Stockcode', 'N/A'))
                    price = float(product.get('Price', 0))
                    product_obj = Product(
                        sku=sku,
                        name=name,
                        price=price
                    )
                    products.append(product_obj)
            return products
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None

    def _handle_request_error(self, response: requests.Response) -> None:
        if response.status_code == 429:
            print("Rate limit exceeded")
            self._rotate_user_agent()
            self._set_cookies(force_refresh=True)
            time.sleep(3)

    def search_products(self, search_query: str, return_first: bool = False, exact_name: str = None, max_retries: int = 3) -> Union[List[Product], Product, None]:
        retries = 0
        while retries < max_retries:
            try:
                session = requests.Session()
                self._set_cookies()
                response = session.post(
                    self.base_url,
                    headers=self._get_headers(),
                    cookies=self.cookies,
                    json=self._get_payload(search_query)
                )

                if response.status_code != 200:
                    retries += 1
                    self._handle_request_error(response)
                    continue

                data = self._parse_response(response.json(), exact_name)
                if data is None or len(data) == 0:
                    print(
                        f"No products found for {search_query} in {self.shop_name}")
                    return None
                if return_first:
                    return data[0]
                return data

            except requests.RequestException as e:
                retries += 1
                print(f"Error making request: {e}")
                self._handle_request_error(response)

            except ValueError as e:
                print(f"Error parsing JSON response: {e}")
                return None

        return None
