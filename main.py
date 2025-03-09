from src.reject_shop import RejectshopScrapper
from src.woolworth import WoolworthScrapper
from src.models.product import Shop, Product
from datetime import datetime
import json
import os

AGGREGATED_DATA_FILE = 'data/aggregated_results.json'


def save_aggregated_data(reject_shop: Shop, woolworths: Shop) -> None:
    aggregated_data = []

    for reject_product in reject_shop.products:
        woolworth_product = next(
            (p for p in woolworths.products if p.uid == reject_product.uid),
            None
        )

        price_difference = None
        cheaper_shop = None
        if woolworth_product:
            price_difference = abs(
                reject_product.price - woolworth_product.price)
            if price_difference is not None:
                price_difference = f"${price_difference:.2f}"
                if reject_product.price < woolworth_product.price:
                    cheaper_shop = "RejectShop"
                elif woolworth_product.price < reject_product.price:
                    cheaper_shop = "Woolworths"

        data = {
            "SKU": reject_product.sku,
            "Product Name": reject_product.name,
            "Price_RejectShop": f"${reject_product.price:.2f}",
            "Price_Woolworths": f"${woolworth_product.price:.2f}" if woolworth_product else None,
            "Price Difference": price_difference,
            "Cheaper Shop": cheaper_shop,
            "Date": datetime.now().strftime("%Y-%m-%d")
        }
        aggregated_data.append(data)

    os.makedirs('data', exist_ok=True)
    with open(AGGREGATED_DATA_FILE, 'w') as f:
        json.dump(aggregated_data, f, indent=2)


def scrap_data(skus: list[str]):
    reject_shop = Shop(shop_name='rejectshop')
    reject_shop_scrapper = RejectshopScrapper()

    for sku in skus:
        reject_shop_product: Product | None = reject_shop_scrapper.search_products(
            sku, return_first=True)
        if reject_shop_product:
            reject_shop.products.append(reject_shop_product)
    reject_shop.save_to_json_file()

    woolworths = Shop(shop_name='woolworths')
    woolworths_scrapper = WoolworthScrapper()

    for reject_shop_product in reject_shop.products:
        product: Product | None = woolworths_scrapper.search_products(
            reject_shop_product.name, return_first=True)
        if product:
            product.uid = reject_shop_product.uid
            woolworths.products.append(product)
    woolworths.save_to_json_file()
    save_aggregated_data(reject_shop, woolworths)


if __name__ == "__main__":
    example_skus = [  # Added some of my own skus to test
        '30087959', '30061292', '30115549', '30121649', '30115976', '30148814', '30140778', '30132927', '30107779', '30113527', '30043588'
    ]
    scrap_data(example_skus)
    print(f"Saved data to {AGGREGATED_DATA_FILE}")
