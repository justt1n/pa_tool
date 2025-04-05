import copy
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Optional


@dataclass
class DD373Product:
    title: str = ""
    url: str = ""
    product_id: str = ""
    server_info: str = ""
    price: float = 0.0
    stock: int = 0
    exchange_rate_1: str = ""  # 1元=17.5439钻
    exchange_rate_2: str = ""  # 1钻=0.0570元
    credit_rating: int = 0  # Trust level (1-15): 1-5 hearts, 6-10 diamonds, 11-15 crowns
    purchase_url: str = ""

    @classmethod
    def from_html_element(cls, item: Tag, domain: str = "https://www.dd373.com") -> "DD373Product":
        """Create a DD373Product instance from a BeautifulSoup Tag element"""
        product = cls()

        # Title and URL
        title_elem = item.select_one('.goods-list-title')
        if title_elem:
            product.title = title_elem.text.strip()
            href = title_elem.get('href', '')
            if href and href.startswith('/'):
                href = f"{domain}{href}"
            product.url = href

            # Product ID
            if '/detail-' in href:
                product.product_id = href.split('/detail-')[1].split('.html')[0]

        # Server info
        server_info = item.select_one('.game-qufu-attr')
        if server_info:
            servers = [a.text.strip() for a in server_info.select('a')]
            product.server_info = '/'.join(servers) if servers else ''

        # Price
        price_elem = item.select_one('.goods-price span')
        if price_elem:
            price_text = price_elem.text.strip()
            try:
                product.price = float(price_text.replace('￥', ''))
            except (ValueError, TypeError):
                product.price = 0.0

        # Stock
        stock_elem = item.select_one('.kucun span')
        if stock_elem:
            try:
                product.stock = int(stock_elem.text.strip())
            except (ValueError, TypeError):
                product.stock = 0

        # Exchange rates
        rates_div = item.select_one('.width233')
        if rates_div:
            rate_texts = [p.text.strip() for p in rates_div.select('p')]
            if len(rate_texts) >= 2:
                product.exchange_rate_1 = rate_texts[0]
                product.exchange_rate_2 = rate_texts[1]

        # Credit rating based on icon type and count
        reputation = item.select_one('.game-reputation')
        if reputation:
            hearts = len(reputation.select('i.icon-heart'))
            diamonds = len(reputation.select('i.icon-bluediamond'))
            crowns = len(reputation.select('i.icon-crown'))

            # Calculate actual level based on icon type and count
            if hearts > 0:
                # Levels 1-5: represented by 1-5 hearts
                product.credit_rating = hearts
            elif diamonds > 0:
                # Levels 6-10: represented by 1-5 diamonds
                product.credit_rating = 5 + diamonds
            elif crowns > 0:
                # Levels 11-15: represented by 1-5 crowns
                product.credit_rating = 10 + crowns

        # Purchase URL
        buy_btn = item.select_one('.shop-btn-group a.im-buy-btn')
        if buy_btn:
            href = buy_btn.get('href', '')
            if href and not href.startswith('http'):
                href = f"https:{href}"
            product.purchase_url = href

        return product

    def to_dict(self) -> Dict[str, Any]:
        """Convert the product to a dictionary"""
        return asdict(self)


def get_dd373_listings(url: str) -> List[DD373Product]:
    """
    Scrapes product listings from DD373 website

    Args:
        url: The DD373 URL to scrape

    Returns:
        A list of DD373Product objects
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # Extract domain for complete URLs
    domain = url.split('/s-')[0] if '/s-' in url else 'https://www.dd373.com'

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all product listings
    goods_list_items = soup.select('div.goods-list-item')

    # Create product objects from HTML elements
    return [DD373Product.from_html_element(item, domain) for item in goods_list_items]


def _filter_valid_offer_item(listOffers: List[DD373Product]) -> List[DD373Product]:
    # Make a copy of the list
    offers_copy = copy.deepcopy(listOffers)

    # Sort by exchange_rate_2
    sorted_offers = sorted(offers_copy, key=lambda x: float(x.exchange_rate_2.split('=')[1].replace('元', '').strip()))

    # Filter sellers with credit_rating < 5
    valid_offers = [offer for offer in sorted_offers if offer.credit_rating < 5]

    return valid_offers



if __name__ == "__main__":
    url = "https://www.dd373.com/s-9fv09v-5tgdjq-55ns9v-0-0-0-3xb9qq-0-0-0-0-0-1-0-3-0.html"
    listings = get_dd373_listings(url)
    for listing in listings:
        print(listing)