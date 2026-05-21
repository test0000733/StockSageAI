import pandas as pd
import numpy as np
import os
import logging
from glob import glob
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class StockDataLoader:
    """Advanced stock data loader for NSE and BSE stocks with intelligent deduplication"""

    def __init__(self, nse_csv_path: str = None, bse_csv_path: str = None):
        self.package_dir = os.path.dirname(__file__)
        self.project_root = os.path.abspath(os.path.join(self.package_dir, os.pardir))

        self.nse_csv_path = self._resolve_csv_path(
            nse_csv_path,
            default_name='EQUITY_L(in).csv',
            alternate_patterns=['EQUITY_L(in).csv', 'EQUITY_L*.csv']
        )
        self.bse_csv_path = self._resolve_csv_path(
            bse_csv_path,
            default_name='EQUITY_L.csv',
            alternate_patterns=['EQUITY_L.csv', 'EQUITY_L*.csv']
        )
        self.master_dataset = None
        self.symbol_to_stock = {}
        self.name_to_stock = {}
        self.isin_to_stock = {}

    def _resolve_csv_path(self, path: Optional[str], default_name: str, alternate_patterns: list) -> Optional[str]:
        """Resolve a CSV path using package and project root fallbacks."""
        candidates = []
        if path:
            candidates.append(path)
            if not os.path.isabs(path):
                candidates.append(os.path.join(self.package_dir, path))
                candidates.append(os.path.join(self.project_root, path))
        else:
            candidates.append(os.path.join(self.package_dir, default_name))
            candidates.append(os.path.join(self.project_root, default_name))

        # Search exact candidates first
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return os.path.abspath(candidate)

        # Search for matching alternate filenames in package and project directories
        search_dirs = [self.package_dir, self.project_root]
        for search_dir in search_dirs:
            for pattern in alternate_patterns:
                for match in glob(os.path.join(search_dir, pattern)):
                    if os.path.exists(match):
                        return os.path.abspath(match)

        logger.warning(
            f"CSV not found for {default_name}. Tried: {candidates} and patterns {alternate_patterns} in {search_dirs}"
        )
        return path

    def clean_stock_name(self, name: str) -> str:
        """Clean and standardize stock names"""
        if not name or not isinstance(name, str):
            return ""

        # Remove extra spaces and normalize
        name = re.sub(r'\s+', ' ', name.strip())

        # Handle special characters and standardize
        name = name.upper()

        # Remove common suffixes that might cause duplicates
        name = re.sub(r'\s+LIMITED\s*$', '', name)
        name = re.sub(r'\s+LTD\s*$', '', name)
        name = re.sub(r'\s+CORPORATION\s*$', '', name)
        name = re.sub(r'\s+CORP\s*$', '', name)
        name = re.sub(r'\s+COMPANY\s*$', '', name)
        name = re.sub(r'\s+CO\s*$', '', name)

        return name.strip()

    def load_csv_file(self, file_path: Optional[str], exchange: str) -> pd.DataFrame:
        """Load and preprocess a single CSV file"""
        if not file_path or not os.path.exists(file_path):
            logger.error(f"CSV file not found for {exchange}: {file_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_path)

            # Standardize column names
            df.columns = df.columns.str.strip().str.upper()

            # Ensure required columns exist
            required_cols = ['SYMBOL', 'NAME OF COMPANY', 'ISIN NUMBER']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing columns in {file_path}: {missing_cols}")
                return pd.DataFrame()

            # Clean and prepare data
            df = df.copy()
            df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
            df['NAME OF COMPANY'] = df['NAME OF COMPANY'].astype(str).str.strip()
            df['ISIN NUMBER'] = df['ISIN NUMBER'].astype(str).str.strip().str.upper()
            df['EXCHANGE'] = exchange
            df['CLEAN_NAME'] = df['NAME OF COMPANY'].apply(self.clean_stock_name)

            # Add searchable text (combination of symbol and name)
            df['SEARCH_TEXT'] = df.apply(
                lambda row: f"{row['SYMBOL']} {row['NAME OF COMPANY']} {row['CLEAN_NAME']}",
                axis=1
            )

            logger.info(f"Loaded {len(df)} stocks from {exchange}")
            return df

        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()

    def merge_datasets(self, nse_df: pd.DataFrame, bse_df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently merge NSE and BSE datasets with deduplication"""
        if nse_df.empty and bse_df.empty:
            return pd.DataFrame()

        # Combine datasets
        combined_df = pd.concat([nse_df, bse_df], ignore_index=True)

        if combined_df.empty:
            return pd.DataFrame()

        # Remove duplicates based on multiple criteria
        # Priority: NSE > BSE for duplicates
        combined_df['PRIORITY'] = combined_df['EXCHANGE'].map({'NSE': 1, 'BSE': 0})

        # Sort by priority and keep the first occurrence for each unique identifier
        deduped_df = combined_df.sort_values(['ISIN NUMBER', 'SYMBOL', 'CLEAN_NAME', 'PRIORITY'],
                                           ascending=[True, True, True, False])

        # Remove duplicates keeping the highest priority entry
        deduped_df = deduped_df.drop_duplicates(subset=['ISIN NUMBER'], keep='first')
        deduped_df = deduped_df.drop_duplicates(subset=['SYMBOL'], keep='first')

        # Final cleanup
        deduped_df = deduped_df.drop(columns=['PRIORITY'])
        deduped_df = deduped_df.reset_index(drop=True)

        logger.info(f"Merged datasets: {len(deduped_df)} unique stocks")
        return deduped_df

    def build_search_indices(self, df: pd.DataFrame):
        """Build efficient search indices"""
        if df.empty:
            return

        # Symbol to stock mapping (convert Series to dict)
        self.symbol_to_stock = {
            row['SYMBOL']: row.to_dict() for _, row in df.iterrows()
        }

        # Name to stock mapping (convert Series to dict)
        self.name_to_stock = {
            row['CLEAN_NAME']: row.to_dict() for _, row in df.iterrows()
        }

        # ISIN to stock mapping (convert Series to dict)
        self.isin_to_stock = {
            row['ISIN NUMBER']: row.to_dict() for _, row in df.iterrows()
        }

        # Create searchable terms list for fuzzy matching
        self.search_terms = []
        for _, row in df.iterrows():
            self.search_terms.append({
                'symbol': row['SYMBOL'],
                'name': row['NAME OF COMPANY'],
                'clean_name': row['CLEAN_NAME'],
                'search_text': row['SEARCH_TEXT'],
                'isin': row['ISIN NUMBER'],
                'exchange': row['EXCHANGE'],
                'data': row.to_dict()
            })

    def load_and_process_data(self) -> pd.DataFrame:
        """Main method to load and process all stock data"""
        logger.info("Loading stock data from CSV files...")
        logger.info(f"Resolved NSE CSV path: {self.nse_csv_path}")
        logger.info(f"Resolved BSE CSV path: {self.bse_csv_path}")

        # Load both datasets
        nse_df = self.load_csv_file(self.nse_csv_path, 'NSE')
        bse_df = self.load_csv_file(self.bse_csv_path, 'BSE')

        # Merge and deduplicate
        self.master_dataset = self.merge_datasets(nse_df, bse_df)

        if not self.master_dataset.empty:
            # Build search indices
            self.build_search_indices(self.master_dataset)
            logger.info(f"Successfully loaded {len(self.master_dataset)} stocks")
        else:
            logger.error("No stock data loaded")

        return self.master_dataset

    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get stock data by symbol"""
        symbol = symbol.upper().strip()
        return self.symbol_to_stock.get(symbol)

    def get_stock_by_name(self, name: str) -> Optional[Dict]:
        """Get stock data by cleaned name"""
        name = self.clean_stock_name(name)
        return self.name_to_stock.get(name)

    def get_stock_by_isin(self, isin: str) -> Optional[Dict]:
        """Get stock data by ISIN"""
        isin = isin.upper().strip()
        return self.isin_to_stock.get(isin)

    def get_all_stocks(self) -> List[Dict]:
        """Get all stocks as list of dictionaries"""
        if self.master_dataset is None or self.master_dataset.empty:
            return []
        return self.master_dataset.to_dict('records')

    def get_popular_stocks(self, limit: int = 20) -> List[Dict]:
        """Get popular stocks (can be extended with real popularity metrics)"""
        if self.master_dataset is None or self.master_dataset.empty:
            return []

        # For now, return a mix of well-known stocks
        popular_symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'HINDUNILVR',
            'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'BAJFINANCE',
            'BHARTIARTL', 'HCLTECH', 'WIPRO', 'NTPC', 'POWERGRID', 'ONGC',
            'COALINDIA', 'GRASIM'
        ]

        popular_stocks = []
        for symbol in popular_symbols:
            stock = self.get_stock_by_symbol(symbol)
            if stock is not None:
                popular_stocks.append(stock)
            if len(popular_stocks) >= limit:
                break

        return popular_stocks

    def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """Basic search method (will be enhanced by the search engine)"""
        if not query or self.master_dataset is None or self.master_dataset.empty:
            return []

        query = query.upper().strip()
        if not query:
            return []

        # Simple exact match search
        results = []
        for _, row in self.master_dataset.iterrows():
            if (query in row['SYMBOL'] or
                query in row['NAME OF COMPANY'].upper() or
                query in row['CLEAN_NAME']):
                results.append(row.to_dict())
                if len(results) >= limit:
                    break

        return results