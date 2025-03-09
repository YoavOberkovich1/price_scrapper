import requests
from typing import List, Union
from src.models.product import Product
from src.shopify_token import ShopifyTokenManager
from src.models.base_scrapper import BaseScrapper
import time


class RejectshopScrapper(BaseScrapper):
    def __init__(self) -> None:
        super().__init__()
        self.base_url = 'https://therejectshop.myshopify.com/api/2024-07/graphql.json'
        self.token_manager = ShopifyTokenManager('therejectshop.myshopify.com')
        self.current_token = self.token_manager.get_token()

    def _get_new_refresh_token(self):
        self.current_token = self.token_manager.get_token(force_refresh=True)

    def _get_headers(self) -> dict:
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://therejectshop.myshopify.com',
            'referer': 'https://therejectshop.myshopify.com/',
            'user-agent': self.current_user_agent,
            'x-shopify-storefront-access-token': self.current_token
        }

    def _get_query(self, search_query: str) -> dict:
        query = """
            query search(
                $query: String!
                $filters: [ProductFilter!]
                $first: Int
                $after: String
                $sortKey: SearchSortKeys
                $reverse: Boolean
            ) {
                search(
                    query: $query
                    productFilters: $filters
                    first: $first
                    after: $after
                    sortKey: $sortKey
                    reverse: $reverse
                    types: [PRODUCT]
                ) {
                    edges {
                        node {
                            ... on Product {
                                id
                                title
                                handle
                                variants(first: 1) {
                                    edges {
                                        node {
                                            sku
                                            price {
                                                amount
                                                currencyCode
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

        variables = {
            "query": search_query,
            "first": 4,
            "filters": [
                {
                    "productMetafield": {
                        "namespace": "custom",
                        "key": "product_lifecycle_status",
                        "value": "Active"
                    }
                },
                {
                    "productMetafield": {
                        "namespace": "custom",
                        "key": "product_lifecycle_status",
                        "value": "active"
                    }
                }
            ],
            "after": None,
            "sortKey": None,
            "reverse": False
        }

        return {"query": query, "variables": variables}

    def _parse_response(self, results: dict) -> Union[list[Product], None]:
        try:
            products = []
            if 'data' not in results or 'search' not in results['data']:
                return None
            for edge in results['data']['search']['edges']:
                product = edge['node']
                if not product['variants']['edges']:
                    continue
                variant = product['variants']['edges'][0]['node']
                price = variant['price']
                sku = variant.get('sku', 'N/A')
                products.append(Product(
                    sku=sku,
                    name=product['title'],
                    price=price['amount'],
                ))
            return products
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None

    def search_products(self, search_query: str, max_retries: int = 3, return_first: bool = False) -> Union[List[Product], Product, None]:
        retries = 0
        while retries < max_retries:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=self._get_query(search_query),
                timeout=10
            )

            if response.status_code == 200:
                parsed = self._parse_response(response.json())
                if parsed is None or len(parsed) == 0:
                    print(
                        f"No products found for {search_query} in {self.shop_name}")
                    return None
                if return_first:
                    return parsed[0]
                return parsed

            elif response.status_code == 401:
                self._get_new_refresh_token()
            elif response.status_code == 429:
                self._rotate_user_agent()
            retries += 1
            if retries < max_retries:
                time.sleep(1)
        return None
