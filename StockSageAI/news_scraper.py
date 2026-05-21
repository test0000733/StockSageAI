import requests
import trafilatura
from datetime import datetime, timedelta
import re
import time
import streamlit as st
from bs4 import BeautifulSoup
import os

class NewsScraper:
    """Scrape financial news from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # News sources
        self.sources = [
            'moneycontrol.com',
            'economictimes.indiatimes.com',
            'business-standard.com',
            'livemint.com'
        ]
    
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def get_news(_self, company_name, days_back=7, max_headlines=20):
        """
        Get news headlines for a company
        
        Args:
            company_name: Name of the company
            days_back: Number of days to look back
            max_headlines: Maximum number of headlines to return
        
        Returns:
            List of news headline dictionaries
        """
        headlines = []
        
        try:
            # Try NewsAPI first if API key is available
            api_headlines = _self._get_newsapi_headlines(company_name, days_back)
            headlines.extend(api_headlines)
            
            # If not enough headlines, try web scraping
            if len(headlines) < max_headlines // 2:
                scraped_headlines = _self._scrape_financial_news(company_name, days_back)
                headlines.extend(scraped_headlines)
            
            # Remove duplicates and sort by date
            unique_headlines = _self._remove_duplicates(headlines)
            sorted_headlines = sorted(
                unique_headlines, 
                key=lambda x: x.get('date', ''), 
                reverse=True
            )
            
            return sorted_headlines[:max_headlines]
            
        except Exception as e:
            st.warning(f"Error fetching news: {str(e)}")
            return []
    
    def _get_newsapi_headlines(self, company_name, days_back):
        """Get headlines from NewsAPI"""
        headlines = []
        
        try:
            # Get API key from environment
            api_key = os.getenv('NEWS_API_KEY')
            
            if not api_key:
                return headlines
            
            # Calculate date range
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # Search query
            query = f'"{company_name}" OR "{company_name} stock" OR "{company_name} shares"'
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': from_date,
                'to': to_date,
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': api_key,
                'pageSize': 50
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('articles', []):
                    if self._is_relevant_financial_news(article.get('title', ''), company_name):
                        headline = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'source': article.get('source', {}).get('name', 'NewsAPI'),
                            'url': article.get('url', ''),
                            'date': article.get('publishedAt', '')[:10]  # YYYY-MM-DD format
                        }
                        headlines.append(headline)
            
        except Exception as e:
            print(f"NewsAPI error: {e}")
        
        return headlines
    
    def _scrape_financial_news(self, company_name, days_back):
        """Scrape news from Indian financial websites"""
        headlines = []
        
        # Search URLs for different sources
        search_urls = [
            f"https://www.moneycontrol.com/news/tags/{company_name.lower()}.html",
            f"https://economictimes.indiatimes.com/topic/{company_name}",
        ]
        
        for url in search_urls:
            try:
                time.sleep(1)  # Rate limiting
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract headlines based on site structure
                    if 'moneycontrol' in url:
                        site_headlines = self._extract_moneycontrol_headlines(soup, company_name)
                    elif 'economictimes' in url:
                        site_headlines = self._extract_et_headlines(soup, company_name)
                    else:
                        site_headlines = []
                    
                    headlines.extend(site_headlines)
                    
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue
        
        return headlines
    
    def _extract_moneycontrol_headlines(self, soup, company_name):
        """Extract headlines from MoneyControl"""
        headlines = []
        
        try:
            # Look for news items
            news_items = soup.find_all(['div', 'article'], class_=re.compile(r'news|article|item'))
            
            for item in news_items[:10]:  # Limit to first 10
                title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'], string=re.compile(company_name, re.I))
                
                if not title_elem:
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    
                    if self._is_relevant_financial_news(title, company_name):
                        headline = {
                            'title': title,
                            'description': '',
                            'source': 'MoneyControl',
                            'url': '',
                            'date': datetime.now().strftime('%Y-%m-%d')
                        }
                        headlines.append(headline)
                        
        except Exception as e:
            print(f"Error extracting MoneyControl headlines: {e}")
        
        return headlines
    
    def _extract_et_headlines(self, soup, company_name):
        """Extract headlines from Economic Times"""
        headlines = []
        
        try:
            # Look for news items
            news_items = soup.find_all(['div', 'article'], class_=re.compile(r'story|news|article'))
            
            for item in news_items[:10]:  # Limit to first 10
                title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    
                    if self._is_relevant_financial_news(title, company_name):
                        headline = {
                            'title': title,
                            'description': '',
                            'source': 'Economic Times',
                            'url': '',
                            'date': datetime.now().strftime('%Y-%m-%d')
                        }
                        headlines.append(headline)
                        
        except Exception as e:
            print(f"Error extracting ET headlines: {e}")
        
        return headlines
    
    def _is_relevant_financial_news(self, title, company_name):
        """Check if news title is relevant to the company and financial"""
        if not title:
            return False
        
        title_lower = title.lower()
        company_lower = company_name.lower()
        
        # Check if company name is mentioned
        company_mentioned = (
            company_lower in title_lower or
            any(word in title_lower for word in company_lower.split())
        )
        
        # Check for financial keywords
        financial_keywords = [
            'stock', 'share', 'price', 'market', 'trading', 'earnings', 'profit',
            'revenue', 'quarterly', 'financial', 'investment', 'analyst', 'rating',
            'upgrade', 'downgrade', 'target', 'dividend', 'acquisition', 'merger',
            'ipo', 'results', 'guidance', 'outlook', 'forecast'
        ]
        
        has_financial_keywords = any(keyword in title_lower for keyword in financial_keywords)
        
        # Filter out irrelevant content
        irrelevant_keywords = [
            'recipe', 'weather', 'sports', 'entertainment', 'movie', 'celebrity',
            'fashion', 'travel', 'health', 'lifestyle'
        ]
        
        has_irrelevant_keywords = any(keyword in title_lower for keyword in irrelevant_keywords)
        
        return company_mentioned and (has_financial_keywords or not has_irrelevant_keywords)
    
    def _remove_duplicates(self, headlines):
        """Remove duplicate headlines based on title similarity"""
        unique_headlines = []
        seen_titles = set()
        
        for headline in headlines:
            title = headline.get('title', '').lower().strip()
            
            # Create a simplified version for comparison
            simplified_title = re.sub(r'[^\w\s]', '', title)
            simplified_title = ' '.join(simplified_title.split())
            
            if simplified_title and simplified_title not in seen_titles:
                seen_titles.add(simplified_title)
                unique_headlines.append(headline)
        
        return unique_headlines
    
    def get_sample_headlines(self, company_name):
        """Generate sample headlines for testing (fallback)"""
        sample_headlines = [
            {
                'title': f'{company_name} reports strong quarterly earnings',
                'description': f'{company_name} exceeded analyst expectations with robust performance',
                'source': 'Financial Times',
                'date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'title': f'Analysts upgrade {company_name} rating to buy',
                'description': f'Leading brokerage firms raise price targets for {company_name}',
                'source': 'Market Watch',
                'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            },
            {
                'title': f'{company_name} stock shows resilient performance',
                'description': f'{company_name} maintains steady growth amid market volatility',
                'source': 'Business Standard',
                'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            }
        ]
        
        return sample_headlines
