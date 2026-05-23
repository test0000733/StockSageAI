import streamlit as st
import pandas as pd
import time
import logging
from typing import List, Dict, Optional, Callable
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedStockSearch:
    """Advanced stock search component with autocomplete and modern UI"""

    def __init__(self, search_engine, data_loader):
        self.search_engine = search_engine
        self.data_loader = data_loader
        self.search_history = []
        self.recent_searches = []
        self.selected_stock = None

        # Initialize session state
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'show_dropdown' not in st.session_state:
            st.session_state.show_dropdown = False
        if 'selected_index' not in st.session_state:
            st.session_state.selected_index = -1

    def render_search_styles(self):
        """Render custom CSS styles for the search component"""
        st.markdown("""
        <style>
        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes shimmer { 0% { background-position: -1000px 0; } 100% { background-position: 1000px 0; } }
        @keyframes glow { 0% { box-shadow: 0 0 5px rgba(56,189,248,0.3); } 50% { box-shadow: 0 0 20px rgba(56,189,248,0.6); } 100% { box-shadow: 0 0 5px rgba(56,189,248,0.3); } }
        
        .search-container {
            position: relative;
            max-width: 800px;
            margin: 0 auto 2rem;
            z-index: 1000;
            animation: slideIn 0.5s ease;
        }

        .search-input-container {
            position: relative;
            background: linear-gradient(135deg, rgba(30,41,59,0.6), rgba(15,23,42,0.6));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(56,189,248,0.3);
            border-radius: 16px;
            padding: 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .search-input-container:focus-within {
            border-color: rgba(56,189,248,0.8);
            box-shadow: 0 8px 32px rgba(56,189,248,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
            transform: translateY(-2px);
            animation: glow 2s ease-in-out;
        }

        .search-input-container .stTextInput>div>div>input,
        .search-input-container .stTextInput>div>div>textarea {
            width: 100% !important;
            padding: 1rem 3rem 1rem 3rem !important;
            border: none !important;
            background: transparent !important;
            color: #e0f7ff !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
            outline: none !important;
            box-shadow: none !important;
            border-radius: 16px !important;
        }

        .search-input-container .stTextInput>div>div>input::placeholder,
        .search-input-container .stTextInput>div>div>textarea::placeholder {
            color: rgba(226,239,255,0.5) !important;
        }

        .search-input-container .stTextInput>div>div>input:focus,
        .search-input-container .stTextInput>div>div>textarea:focus {
            outline: none !important;
            box-shadow: none !important;
        }

        .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: rgba(56,189,248,0.9);
            font-size: 1.2rem;
            z-index: 1;
        }

        .clear-button {
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(239,68,68,0.2);
            border: 1px solid rgba(239,68,68,0.3);
            color: #ef4444;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        }

        .clear-button:hover {
            background: rgba(239,68,68,0.3);
            transform: translateY(-50%) scale(1.1);
        }

        .search-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: rgba(10,16,31,0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            max-height: 400px;
            overflow-y: auto;
            z-index: 1001;
            margin-top: 0.5rem;
            animation: slideDown 0.2s ease-out;
        }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .search-result-item {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .search-result-item:last-child {
            border-bottom: none;
        }

        .search-result-item:hover {
            background: rgba(56,189,248,0.1);
            border-left: 3px solid #38bdf8;
        }

        .search-result-item.selected {
            background: rgba(56,189,248,0.15);
            border-left: 3px solid #38bdf8;
        }

        .stock-symbol {
            font-weight: 600;
            color: #38bdf8;
            font-size: 0.95rem;
        }

        .stock-name {
            color: #e0f7ff;
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }

        .stock-exchange {
            color: rgba(226,239,255,0.6);
            font-size: 0.8rem;
            background: rgba(255,255,255,0.05);
            padding: 0.2rem 0.5rem;
            border-radius: 8px;
        }

        .popular-stocks-section {
            margin-top: 2rem;
        }

        .popular-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #e0f7ff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .stock-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }

        .stock-chip {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            color: #e0f7ff;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .stock-chip:hover {
            background: rgba(56,189,248,0.2);
            border-color: rgba(56,189,248,0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(56,189,248,0.2);
        }

        .stock-chip .chip-symbol {
            font-weight: 600;
            color: #38bdf8;
        }

        .recent-searches {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,0.08);
        }

        .recent-title {
            font-size: 1rem;
            color: rgba(226,239,255,0.8);
            margin-bottom: 0.5rem;
        }

        .recent-item {
            display: inline-block;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 0.4rem 0.8rem;
            margin: 0.25rem 0.5rem 0.25rem 0;
            color: rgba(226,239,255,0.7);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }

        .recent-item:hover {
            background: rgba(56,189,248,0.1);
            color: #38bdf8;
        }

        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #38bdf8;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Badge styles */
        .badge-nse {
            display: inline-block;
            background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(16,185,129,0.2));
            border: 1px solid rgba(34,197,94,0.4);
            color: #10b981;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }

        .badge-bse {
            display: inline-block;
            background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(139,92,246,0.2));
            border: 1px solid rgba(168,85,247,0.4);
            color: #c084fc;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }

        /* Skeleton loader styles */
        .skeleton-card {
            background: linear-gradient(90deg, rgba(255,255,255,0.08) 25%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.08) 75%);
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
            border-radius: 8px;
            height: 60px;
            margin-bottom: 10px;
        }

        .skeleton-line {
            background: linear-gradient(90deg, rgba(255,255,255,0.08) 25%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.08) 75%);
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
            border-radius: 6px;
            height: 12px;
            margin-bottom: 8px;
            width: 80%;
        }

        .skeleton-line-short {
            width: 40%;
        }

        /* Result card enhancement */
        .result-card {
            background: linear-gradient(135deg, rgba(30,41,59,0.4), rgba(15,23,42,0.4));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(56,189,248,0.2);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeIn 0.4s ease;
        }

        .result-card:hover {
            background: linear-gradient(135deg, rgba(30,41,59,0.6), rgba(15,23,42,0.6));
            border-color: rgba(56,189,248,0.4);
            box-shadow: 0 8px 25px rgba(56,189,248,0.15);
            transform: translateY(-2px);
        }

        .result-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }

        .result-symbol {
            font-weight: 700;
            color: #38bdf8;
            font-size: 1rem;
        }

        .result-exchange {
            font-size: 0.75rem;
            font-weight: 600;
        }

        .result-name {
            color: rgba(226,239,255,0.8);
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }

        /* Popular stocks grid enhancement */
        .popular-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .popular-card {
            background: linear-gradient(135deg, rgba(30,41,59,0.5), rgba(15,23,42,0.5));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(56,189,248,0.25);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: slideIn 0.5s ease;
        }

        .popular-card:hover {
            background: linear-gradient(135deg, rgba(30,41,59,0.7), rgba(15,23,42,0.7));
            border-color: rgba(56,189,248,0.5);
            box-shadow: 0 12px 30px rgba(56,189,248,0.2);
            transform: translateY(-4px);
        }

        .popular-symbol {
            font-weight: 700;
            color: #38bdf8;
            font-size: 1.05rem;
            margin-bottom: 0.3rem;
        }

        .popular-name {
            color: rgba(226,239,255,0.6);
            font-size: 0.8rem;
            line-height: 1.2;
        }

        /* Search stats */
        .search-stats {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            color: rgba(226,239,255,0.7);
        }

        .stats-icon {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: rgba(34,197,94,0.8);
            border-radius: 50%;
            margin-right: 0.5rem;
            animation: pulse 2s ease-in-out infinite;
        }

        .no-results {
            padding: 2rem 1rem;
            text-align: center;
            color: rgba(226,239,255,0.6);
        }

        .no-results-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .search-input {
                font-size: 1rem;
                padding: 0.875rem 2.5rem 0.875rem 2.5rem;
            }

            .search-icon {
                left: 0.75rem;
                font-size: 1.1rem;
            }

            .clear-button {
                right: 0.75rem;
            }

            .stock-chips {
                gap: 0.5rem;
            }

            .stock-chip {
                padding: 0.4rem 0.8rem;
                font-size: 0.85rem;
            }

            .popular-grid {
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: 0.75rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def get_exchange_badge(self, exchange: str) -> str:
        """Get exchange badge HTML with color coding"""
        if exchange == 'NSE':
            return '<span class="badge-nse">NSE</span>'
        if exchange == 'BSE':
            return '<span class="badge-bse">BSE</span>'
        return '<span class="badge-nse">NSE</span>'

    def get_sector_mapping(self, symbol: str) -> str:
        """Get stock sector label for enhanced UI"""
        sectors = {
            'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT', 'TECHM': 'IT',
            'RELIANCE': 'Energy', 'ONGC': 'Energy', 'BPCL': 'Energy', 'IOC': 'Energy',
            'HDFCBANK': 'Finance', 'ICICIBANK': 'Finance', 'SBIN': 'Finance', 'AXISBANK': 'Finance', 'KOTAKBANK': 'Finance',
            'ITC': 'FMCG', 'HINDUNILVR': 'FMCG', 'BRITANNIA': 'FMCG', 'NESTLEIND': 'FMCG',
            'MARUTI': 'Auto', 'BAJAJ-AUTO': 'Auto', 'TATAMOTORS': 'Auto', 'EICHERMOT': 'Auto',
            'LT': 'Infrastructure', 'BHARTIARTL': 'Telecom', 'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
        }
        return sectors.get(symbol, 'Other')

    def render_search_stats(self, query: str, results_count: int):
        """Render current search statistics"""
        if not query or results_count == 0:
            return
        st.markdown(f"""
            <div class="search-stats">
                <span class="stats-icon"></span>
                Showing <strong>{results_count}</strong> result{'s' if results_count != 1 else ''} for "<strong>{query}</strong>"
            </div>
        """, unsafe_allow_html=True)

    def render_skeleton_loader(self, count: int = 3):
        """Render skeleton loading animation"""
        for _ in range(count):
            st.markdown('<div class="skeleton-card"></div>', unsafe_allow_html=True)

    def highlight_match(self, text: str, query: str) -> str:
        """Highlight matching text in search results"""
        if not query:
            return text

        query = re.escape(query)
        highlighted = re.sub(
            f'({query})',
            r'<mark style="background: rgba(56,189,248,0.3); color: #38bdf8; padding: 0 2px; border-radius: 2px;">\1</mark>',
            text,
            flags=re.IGNORECASE
        )
        return highlighted

    def render_search_input(self):
        """Render the main search input with autocomplete"""
        st.markdown('<div class="search-container">', unsafe_allow_html=True)

        # Search input container
        st.markdown('<div class="search-input-container">', unsafe_allow_html=True)

        # Search icon
        st.markdown('<div class="search-icon">🔍</div>', unsafe_allow_html=True)

        # Search input
        query = st.text_input(
            "Search Stock",
            value=st.session_state.get('search_query', ''),
            key="stock_search_input",
            placeholder="Search stocks by symbol or company name (e.g., RELIANCE, TCS, HDFC)...",
            label_visibility="collapsed",
            on_change=self._on_search_change
        )

        search_query = st.session_state.get('search_query', '')

        # Clear button
        if search_query:
            if st.button("×", key="clear_search", help="Clear search"):
                self.clear_search()

        st.markdown('</div>', unsafe_allow_html=True)

        search_query = st.session_state.get('search_query', '')
        if search_query and len(search_query.strip()) >= 2:
            if st.session_state.get('search_results'):
                self.render_search_stats(search_query, len(st.session_state.get('search_results', [])))
                self.render_dropdown()
            else:
                st.markdown(
                    '<div class="no-results"><div class="no-results-icon">😕</div>No matching stock found. Try another keyword.</div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

    def render_dropdown(self):
        """Render the autocomplete dropdown with interactive buttons"""
        st.markdown('<div class="search-dropdown">', unsafe_allow_html=True)

        search_query = st.session_state.get('search_query', '')
        for i, stock in enumerate(st.session_state.get('search_results', [])[:8]):  # Limit to 8 results
            symbol = stock.get('SYMBOL', '')
            name = stock.get('NAME OF COMPANY', '')
            exchange = stock.get('EXCHANGE', '')
            sector = self.get_sector_mapping(symbol)

            highlighted_symbol = self.highlight_match(symbol, search_query)
            highlighted_name = self.highlight_match(name, search_query)
            exchange_badge = self.get_exchange_badge(exchange)

            result_html = f"""
                <div class="result-card">
                    <div class="result-header">
                        <div>
                            <div class="result-symbol">{highlighted_symbol} {exchange_badge}</div>
                            <div class="result-name">{highlighted_name}</div>
                        </div>
                        <div class="result-exchange">{sector}</div>
                    </div>
                </div>
            """

            st.markdown(result_html, unsafe_allow_html=True)
            if st.button(f"Analyze {symbol}", key=f"analyze_btn_{i}", use_container_width=True):
                st.session_state.current_stock = symbol
                if hasattr(self, 'on_stock_select') and self.on_stock_select:
                    self.on_stock_select(stock)

        st.markdown('</div>', unsafe_allow_html=True)

    def render_popular_stocks(self):
        """Render popular stocks section with interactive buttons"""
        st.markdown('<div class="popular-stocks-section">', unsafe_allow_html=True)

        st.markdown("""
        <div class="popular-title">
            🔥 Popular Stocks
        </div>
        """, unsafe_allow_html=True)

        popular_stocks = self.data_loader.get_popular_stocks(12)

        if popular_stocks:
            cols = st.columns(3)
            for idx, stock in enumerate(popular_stocks):
                symbol = stock.get('SYMBOL', '')
                name = stock.get('NAME OF COMPANY', '')
                exchange = stock.get('EXCHANGE', '')
                sector = self.get_sector_mapping(symbol)
                exchange_badge = self.get_exchange_badge(exchange)

                card_content = f"""
                    <div class="popular-card">
                        <div class="popular-symbol">{symbol} {exchange_badge}</div>
                        <div class="popular-name">{name}</div>
                        <div class="result-exchange">{sector}</div>
                    </div>
                """

                with cols[idx % 3]:
                    st.markdown(card_content, unsafe_allow_html=True)
                    if st.button(f"Select {symbol}", key=f"popular_stock_{idx}", use_container_width=True):
                        st.session_state.current_stock = symbol
                        if hasattr(self, 'on_stock_select') and self.on_stock_select:
                            self.on_stock_select(stock)

        st.markdown('</div>', unsafe_allow_html=True)

        # Recent searches
        if self.recent_searches:
            st.markdown('<div class="recent-searches">', unsafe_allow_html=True)
            st.markdown('<div class="recent-title">Recent Searches:</div>', unsafe_allow_html=True)

            for search_term in self.recent_searches[-5:]:  # Show last 5
                if st.button(search_term, key=f"recent_search_{search_term}", width='content'):
                    st.session_state.stock_search_input = search_term
                    self._on_search_change()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _on_search_change(self):
        """Handle search input changes"""
        query = st.session_state.get('stock_search_input', '')
        current_query = st.session_state.get('search_query', '')

        if query != current_query:
            st.session_state.search_query = query

            if len(query.strip()) >= 2:
                # Perform search with correct parameter name
                results = self.search_engine.search(query, limit=10)
                st.session_state.search_results = results
                st.session_state.show_dropdown = len(results) > 0
                st.session_state.selected_index = -1
            else:
                st.session_state.search_results = []
                st.session_state.show_dropdown = False
                st.session_state.selected_index = -1

    def clear_search(self):
        """Clear the search input and results"""
        st.session_state.search_query = ""
        st.session_state.search_results = []
        st.session_state.show_dropdown = False
        st.session_state.selected_index = -1

    def select_stock(self, stock_data: Dict):
        """Handle stock selection"""
        self.selected_stock = stock_data
        self.add_to_recent_searches(stock_data.get('SYMBOL', ''))

        # Add to search history
        if stock_data not in self.search_history:
            self.search_history.append(stock_data)
            if len(self.search_history) > 50:  # Limit history
                self.search_history.pop(0)

        # Clear search
        self.clear_search()

        # Trigger callback if provided
        if hasattr(self, 'on_stock_select'):
            self.on_stock_select(stock_data)

    def add_to_recent_searches(self, search_term: str):
        """Add search term to recent searches"""
        if search_term and search_term not in self.recent_searches:
            self.recent_searches.append(search_term)
            if len(self.recent_searches) > 10:  # Limit to 10 recent searches
                self.recent_searches.pop(0)

    def render(self, on_stock_select: Callable = None):
        """Render the complete search component"""
        self.on_stock_select = on_stock_select

        self.render_search_styles()
        self.render_search_input()
        self.render_popular_stocks()

        return self.selected_stock
