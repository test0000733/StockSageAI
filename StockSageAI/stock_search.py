import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
import re
import time
from functools import lru_cache
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

# Try to import fuzzy matching libraries
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

logger = logging.getLogger(__name__)

class StockSearchEngine:
    """High-performance stock search engine with fuzzy matching and intelligent ranking"""

    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.trie = {}
        self.fuzzy_index = defaultdict(list)
        self._cache = {}
        self._lock = threading.Lock()

    def build_search_index(self):
        """Build search indices for trie and fuzzy matching"""
        if self.data_loader.master_dataset is None or self.data_loader.master_dataset.empty:
            logger.error("No data available to build search index")
            return

        logger.info("Building search index...")
        self._build_trie()
        self._build_fuzzy_index()
        logger.info("Search index built successfully")

    def _build_trie(self):
        """Build trie for prefix matching"""
        self.trie = {}
        for _, row in self.data_loader.master_dataset.iterrows():
            symbol = row['SYMBOL']
            name = row['NAME OF COMPANY']
            isin = row.get('ISIN', '')
            row_dict = row.to_dict()  # Convert Series to dict
            self._insert_into_trie(symbol, row_dict)
            for word in name.split():
                if len(word) > 2:
                    self._insert_into_trie(word, row_dict)
            if isin:
                self._insert_into_trie(isin, row_dict)

    def _insert_into_trie(self, word: str, data: Dict):
        """Insert word into trie"""
        node = self.trie
        word = word.upper()
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        if 'data' not in node:
            node['data'] = []
        node['data'].append(data)

    def _build_fuzzy_index(self):
        """Build fuzzy index for approximate matching"""
        for _, row in self.data_loader.master_dataset.iterrows():
            symbol = row['SYMBOL']
            name = row['NAME OF COMPANY']
            isin = row.get('ISIN', '')
            row_dict = row.to_dict()  # Convert Series to dict
            self.fuzzy_index[symbol].append(row_dict)
            self.fuzzy_index[name].append(row_dict)
            if isin:
                self.fuzzy_index[isin].append(row_dict)

    def _search_trie(self, prefix: str) -> List[Dict]:
        """Search trie for prefix matches"""
        node = self.trie
        prefix = prefix.upper()
        for char in prefix:
            if char not in node:
                return []
            node = node[char]
        return self._collect_trie_data(node)

    def _collect_trie_data(self, node: Dict) -> List[Dict]:
        """Collect all data from trie node and children"""
        results = []
        if 'data' in node:
            results.extend(node['data'])
        for key, child in node.items():
            if key != 'data':
                results.extend(self._collect_trie_data(child))
        return results

    def _calculate_relevance_score(self, query: str, symbol: str, name: str, isin: str) -> float:
        """Calculate relevance score for ranking"""
        query = query.upper()
        symbol = symbol.upper()
        name = name.upper()
        isin = isin.upper() if isin else ''
        score = 0.0
        if query == symbol:
            score += 100.0
        elif symbol.startswith(query):
            score += 80.0
        elif query in symbol:
            score += 60.0
        if query in name:
            score += 40.0
        if query in isin:
            score += 50.0
        if FUZZY_AVAILABLE:
            symbol_fuzz = fuzz.ratio(query, symbol)
            name_fuzz = fuzz.ratio(query, name)
            score += max(symbol_fuzz, name_fuzz) * 0.5
        return score

    def search(self, query: str, limit: int = 10, fuzzy_threshold: float = 0.8) -> List[Dict]:
        """Perform search with fuzzy matching and ranking"""
        if not query or not query.strip():
            return []
        query = query.strip()
        results = []
        # Trie search
        trie_results = self._search_trie(query)
        for data in trie_results:
            score = self._calculate_relevance_score(query, data['SYMBOL'], data['NAME OF COMPANY'], data.get('ISIN', ''))
            results.append((data, score))
        # Fuzzy search
        if FUZZY_AVAILABLE:
            fuzzy_results = process.extract(query, list(self.fuzzy_index.keys()), limit=limit, scorer=fuzz.token_sort_ratio)
            for match, score, _ in fuzzy_results:
                if score / 100 >= fuzzy_threshold:
                    for data in self.fuzzy_index[match]:
                        if data not in [r[0] for r in results]:
                            results.append((data, score))
        # Sort and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """Get autocomplete suggestions"""
        if not prefix or len(prefix) < 2:
            return []
        trie_results = self._search_trie(prefix)
        suggestions = []
        seen = set()
        for data in trie_results[:limit * 2]:
            symbol = data['SYMBOL']
            name = data['NAME OF COMPANY']
            if symbol not in seen and symbol.lower().startswith(prefix.lower()):
                suggestions.append(symbol)
                seen.add(symbol)
            if name not in seen and len(suggestions) < limit:
                suggestions.append(name)
                seen.add(name)
        return suggestions[:limit]

    def cached_search(self, query: str, limit: int = 10, fuzzy_threshold: float = 0.8) -> List[Dict]:
        """Cached search without @lru_cache decorator on instance method"""
        key = (query, limit, fuzzy_threshold)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            result = self.search(query, limit, fuzzy_threshold)
            self._cache[key] = result
            return result
