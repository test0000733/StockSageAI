import re
import pandas as pd
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np

class SentimentAnalyzer:
    """News sentiment analysis using VADER sentiment analyzer"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Add financial domain-specific words to VADER lexicon
        financial_words = {
            'profit': 2.5,
            'loss': -2.5,
            'growth': 2.0,
            'decline': -2.0,
            'bullish': 2.5,
            'bearish': -2.5,
            'rally': 2.0,
            'crash': -3.0,
            'surge': 2.5,
            'plunge': -2.5,
            'acquisition': 1.5,
            'merger': 1.5,
            'bankruptcy': -3.0,
            'dividend': 1.5,
            'earnings': 1.0,
            'revenue': 1.0,
            'upgraded': 2.0,
            'downgraded': -2.0,
            'outperform': 2.0,
            'underperform': -2.0,
            'beat': 1.5,
            'miss': -1.5,
            'positive': 1.5,
            'negative': -1.5,
            'strong': 1.5,
            'weak': -1.5,
            'optimistic': 2.0,
            'pessimistic': -2.0
        }
        
        # Update VADER lexicon with financial terms
        self.analyzer.lexicon.update(financial_words)
    
    def preprocess_text(self, text):
        """Clean and preprocess news text"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\-\%\$]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_sentiment(self, news_headlines):
        """
        Analyze sentiment of news headlines with error handling
        
        Args:
            news_headlines: List of news headline dictionaries
        
        Returns:
            List of sentiment scores with dates
        """
        sentiment_scores = []
        
        if not news_headlines:
            return sentiment_scores
        
        try:
            # Group headlines by date
            daily_headlines = {}
            
            for headline in news_headlines:
                if not headline:
                    continue
                    
                title = headline.get('title', '')
                description = headline.get('description', '')
                date_str = headline.get('date', datetime.now().strftime('%Y-%m-%d'))
                
                # Combine title and description
                full_text = f"{title} {description}".strip()
                
                if not full_text:
                    continue
                
                if date_str not in daily_headlines:
                    daily_headlines[date_str] = []
                
                daily_headlines[date_str].append(full_text)
            
            # Analyze sentiment for each day
            for date_str, headlines in daily_headlines.items():
                daily_sentiments = []
                
                for headline_text in headlines:
                    if headline_text:
                        try:
                            # Preprocess text
                            clean_text = self.preprocess_text(headline_text)
                            
                            if clean_text:
                                # Get sentiment scores
                                scores = self.analyzer.polarity_scores(clean_text)
                                daily_sentiments.append(scores)
                        except Exception as e:
                            # Skip problematic headlines
                            continue
                
                if daily_sentiments:
                    # Calculate average sentiment for the day
                    avg_sentiment = {
                        'date': date_str,
                        'compound': np.mean([s['compound'] for s in daily_sentiments]),
                        'positive': np.mean([s['pos'] for s in daily_sentiments]),
                        'negative': np.mean([s['neg'] for s in daily_sentiments]),
                        'neutral': np.mean([s['neu'] for s in daily_sentiments]),
                        'headline_count': len(daily_sentiments)
                    }
                    
                    sentiment_scores.append(avg_sentiment)
            
            # Sort by date
            sentiment_scores.sort(key=lambda x: x['date'])
            
        except Exception as e:
            # Return empty list on error
            pass
        
        return sentiment_scores
    
    def get_overall_sentiment(self, sentiment_scores):
        """Calculate overall sentiment from daily scores"""
        if not sentiment_scores:
            return {
                'overall_compound': 0.0,
                'sentiment_label': 'Neutral',
                'confidence': 0.0
            }
        
        # Weight recent news more heavily
        weights = []
        compounds = []
        
        for i, score in enumerate(sentiment_scores):
            # More recent news gets higher weight
            weight = 1.0 + (i / len(sentiment_scores)) * 0.5
            weights.append(weight)
            compounds.append(score['compound'])
        
        # Calculate weighted average
        overall_compound = np.average(compounds, weights=weights)
        
        # Determine sentiment label
        if overall_compound >= 0.05:
            sentiment_label = 'Positive'
        elif overall_compound <= -0.05:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'
        
        # Calculate confidence based on consistency
        std_dev = np.std(compounds)
        confidence = max(0.0, min(1.0, 1.0 - float(std_dev)))
        
        return {
            'overall_compound': overall_compound,
            'sentiment_label': sentiment_label,
            'confidence': confidence
        }
    
    def sentiment_impact_factor(self, sentiment_scores):
        """
        Calculate sentiment impact factor for price adjustment
        
        Returns:
            Float between -0.1 and 0.1 representing price impact percentage
        """
        if not sentiment_scores:
            return 0.0
        
        overall_sentiment = self.get_overall_sentiment(sentiment_scores)
        compound_score = overall_sentiment['overall_compound']
        confidence = overall_sentiment['confidence']
        
        # Scale sentiment to impact factor
        # Strong negative sentiment can reduce price by up to 10%
        # Strong positive sentiment can increase price by up to 10%
        max_impact = 0.1  # 10%
        
        impact_factor = compound_score * max_impact * confidence
        
        # Clamp to reasonable bounds
        impact_factor = max(-0.1, min(0.1, impact_factor))
        
        return impact_factor
    
    def analyze_headline_keywords(self, headlines):
        """Extract and analyze key financial keywords from headlines"""
        if not headlines:
            return {}
        
        # Financial keywords to track
        keywords = {
            'positive': ['profit', 'growth', 'rally', 'surge', 'bullish', 'upgraded', 'beat', 'strong', 'positive'],
            'negative': ['loss', 'decline', 'crash', 'plunge', 'bearish', 'downgraded', 'miss', 'weak', 'negative'],
            'neutral': ['earnings', 'revenue', 'dividend', 'announcement', 'result', 'report']
        }
        
        keyword_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        all_text = ' '.join([h.get('title', '') + ' ' + h.get('description', '') for h in headlines])
        all_text = all_text.lower()
        
        for category, word_list in keywords.items():
            for word in word_list:
                keyword_counts[category] += all_text.count(word)
        
        total_keywords = sum(keyword_counts.values())
        
        if total_keywords == 0:
            return keyword_counts
        
        # Calculate percentages
        keyword_percentages = {
            category: (count / total_keywords) * 100
            for category, count in keyword_counts.items()
        }
        
        return keyword_percentages
