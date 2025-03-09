from abc import ABC, abstractmethod
from typing import List, Union
from src.models.product import Product
import random


class BaseScrapper(ABC):
    def __init__(self) -> None:
        self.base_url: str
        self.headers: dict = {}
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        ]
        self.current_user_agent = self.user_agents[0]

    def _rotate_user_agent(self) -> None:
        other_agents = [
            agent for agent in self.user_agents if agent != self.current_user_agent]
        self.current_user_agent = random.choice(other_agents)

    @abstractmethod
    def _get_headers(self) -> dict:
        raise NotImplementedError()

    @abstractmethod
    def _parse_response(self, results: dict) -> Union[List[Product], None]:
        raise NotImplementedError()

    @abstractmethod
    def search_products(self, search_query: str, **kwargs) -> Union[List[Product], Product, None]:
        raise NotImplementedError()
