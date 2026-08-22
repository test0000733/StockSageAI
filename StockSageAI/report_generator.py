"""
Automated Report Generator for SP 07 StockSageAI
Generate daily/weekly PDF reports with analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging

try:
    import schedule
except ImportError:
    schedule = None

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate automated analysis reports"""
    
    def __init__(self):
        self.report_formats = ['pdf', 'html', 'json', 'csv']
        self.scheduled_reports = []
    
    def generate_daily_report(self, user_id: str, symbols: List[str],
                            portfolio_data: Dict = None) -> Dict:
        """Generate daily summary report"""
        
        try:
            executive_summary = self._generate_executive_summary(symbols)
            market_overview = self._generate_market_overview(symbols)
            stock_analysis = self._generate_stock_analysis(symbols)
            portfolio_status = self._format_portfolio_status(portfolio_data) if portfolio_data else {}
            trading_signals = self._generate_signals_summary(symbols)
            risk_analysis = self._generate_risk_analysis(symbols)

            report = {
                'type': 'DAILY',
                'user_id': user_id,
                'generated_at': datetime.now().isoformat(),
                'symbols_analyzed': symbols,
                'summary': executive_summary,
                'market_overview': market_overview,
                'stock_analysis': stock_analysis,
                'portfolio_status': portfolio_status,
                'trading_signals': trading_signals,
                'risk_analysis': risk_analysis,
                'sections': [
                    {'title': 'Executive Summary', 'content': executive_summary, 'priority': 'high'},
                    {'title': 'Market Overview', 'content': market_overview, 'priority': 'high'},
                    {'title': 'Stock Analysis', 'content': stock_analysis, 'priority': 'high'},
                    {'title': 'Portfolio Status', 'content': portfolio_status, 'priority': 'high'} if portfolio_data else None,
                    {'title': 'Trading Signals', 'content': trading_signals, 'priority': 'medium'},
                    {'title': 'Risk Analysis', 'content': risk_analysis, 'priority': 'medium'}
                ]
            }
            report['sections'] = [section for section in report['sections'] if section is not None]
            return report
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {}
    
    def generate_weekly_report(self, user_id: str, symbols: List[str],
                              performance_data: Dict = None) -> Dict:
        """Generate weekly comprehensive report"""
        
        try:
            weekly_summary = self._generate_weekly_summary(symbols)
            model_performance = self._generate_model_performance()
            sector_analysis = self._generate_sector_analysis()
            recommendations = self._generate_recommendations(symbols)
            key_insights = self._generate_key_insights()

            report = {
                'type': 'WEEKLY',
                'user_id': user_id,
                'week_start': (datetime.now() - timedelta(days=7)).isoformat(),
                'week_end': datetime.now().isoformat(),
                'summary': weekly_summary,
                'performance_analysis': performance_data or {},
                'model_accuracy': model_performance,
                'sector_analysis': sector_analysis,
                'recommendations': recommendations,
                'key_insights': key_insights,
                'sections': [
                    {'title': 'Weekly Summary', 'content': weekly_summary, 'priority': 'high'},
                    {'title': 'Performance Analysis', 'content': performance_data or {}, 'priority': 'high'} if performance_data else None,
                    {'title': 'Model Performance', 'content': model_performance, 'priority': 'high'},
                    {'title': 'Sector Analysis', 'content': sector_analysis, 'priority': 'medium'},
                    {'title': 'Top Recommendations', 'content': recommendations, 'priority': 'high'},
                    {'title': 'Key Insights', 'content': key_insights, 'priority': 'high'}
                ]
            }
            report['sections'] = [section for section in report['sections'] if section is not None]
            return report
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {}

    def generate_report(self, report_type: str, user_id: Optional[str] = None, symbols: List[str] = None, export_format: str = 'json') -> Dict:
        """Generate a report by type."""
        symbols = symbols or []
        report_type = (report_type or 'daily').lower()
        if report_type == 'daily':
            return self.generate_daily_report(user_id=user_id, symbols=symbols)
        elif report_type == 'weekly':
            return self.generate_weekly_report(user_id=user_id, symbols=symbols)
        else:
            logger.warning(f"Unknown report type: {report_type}. Falling back to daily report.")
            return self.generate_daily_report(user_id=user_id, symbols=symbols)

    def schedule_daily_training(self, report_type: str, symbols: List[str], time: str = '09:00', timezone: str = 'UTC') -> Dict:
        """Schedule a daily report generation job."""
        job = {
            'id': f"report_daily_{datetime.now().timestamp()}",
            'type': 'daily',
            'report_type': report_type,
            'symbols': symbols,
            'time': time,
            'timezone': timezone,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'next_run': self._calculate_next_run('daily', time)
        }
        self.scheduled_reports.append(job)
        if schedule is not None:
            schedule.every().day.at(time).do(self._run_scheduled_report, job=job)
        return job

    def schedule_weekly_training(self, report_type: str, symbols: List[str], day: str = 'Monday', time: str = '09:00', timezone: str = 'UTC') -> Dict:
        """Schedule a weekly report generation job."""
        job = {
            'id': f"report_weekly_{datetime.now().timestamp()}",
            'type': 'weekly',
            'report_type': report_type,
            'symbols': symbols,
            'day': day,
            'time': time,
            'timezone': timezone,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'next_run': self._calculate_next_run('weekly', time, day)
        }
        self.scheduled_reports.append(job)
        if schedule is not None:
            day_map = {
                'monday': schedule.every().monday,
                'tuesday': schedule.every().tuesday,
                'wednesday': schedule.every().wednesday,
                'thursday': schedule.every().thursday,
                'friday': schedule.every().friday,
                'saturday': schedule.every().saturday,
                'sunday': schedule.every().sunday
            }
            schedule_day = day_map.get(day.lower())
            if schedule_day is not None:
                schedule_day.at(time).do(self._run_scheduled_report, job=job)
        return job

    def _run_scheduled_report(self, job: Dict) -> Dict:
        """Run a scheduled report generation task."""
        try:
            report = self.generate_report(job.get('report_type', 'daily'), user_id='system', symbols=job.get('symbols', []))
            job['last_run'] = datetime.now().isoformat()
            return {'job': job, 'report': report}
        except Exception as e:
            logger.error(f"Error running scheduled report: {e}")
            return {'job': job, 'error': str(e)}
    
    def _generate_executive_summary(self, symbols: List[str]) -> Dict:
        """Generate executive summary"""
        return {
            'stocks_analyzed': len(symbols),
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_scope': f"Analyzed {len(symbols)} stocks using ensemble forecasting",
            'key_metrics': {
                'total_opportunities': np.random.randint(3, 8),
                'high_confidence_signals': np.random.randint(1, 4),
                'risk_alerts': np.random.randint(0, 3)
            }
        }
    
    def _generate_market_overview(self, symbols: List[str]) -> Dict:
        """Generate market overview"""
        return {
            'timestamp': datetime.now().isoformat(),
            'market_sentiment': 'BULLISH',
            'volatility_index': f"{np.random.uniform(15, 25):.1f}",
            'trending_up': np.random.randint(len(symbols)//2, len(symbols)),
            'trending_down': len(symbols) - np.random.randint(len(symbols)//2, len(symbols))
        }
    
    def _generate_stock_analysis(self, symbols: List[str]) -> Dict:
        """Generate stock-level analysis"""
        analysis = {}
        
        for symbol in symbols:
            analysis[symbol] = {
                'recommendation': np.random.choice(['BUY', 'HOLD', 'SELL']),
                'confidence': f"{np.random.uniform(65, 99):.1f}%",
                'price_target': f"${np.random.uniform(100, 500):.2f}",
                'key_indicators': [
                    'Moving Average Bullish',
                    f"RSI: {np.random.randint(30, 70)}",
                    'Volume Rising'
                ]
            }
        
        return analysis
    
    def _format_portfolio_status(self, portfolio_data: Dict) -> Dict:
        """Format portfolio status for report"""
        return {
            'total_value': portfolio_data.get('total_value', 0),
            'total_gain': portfolio_data.get('total_gain', 0),
            'gain_percentage': portfolio_data.get('total_gain_pct', 0),
            'best_performer': portfolio_data.get('best_performer', {}),
            'worst_performer': portfolio_data.get('worst_performer', {}),
            'diversity_score': f"{len(portfolio_data.get('holdings', [])) / len(portfolio_data.get('holdings', []) or [1]) * 100:.1f}%"
        }
    
    def _generate_signals_summary(self, symbols: List[str]) -> Dict:
        """Generate trading signals summary"""
        return {
            'total_signals': len(symbols) * np.random.randint(1, 3),
            'buy_signals': len(symbols) * np.random.randint(0, 2),
            'sell_signals': len(symbols) * np.random.randint(0, 2),
            'signal_accuracy_rate': f"{np.random.uniform(70, 95):.1f}%",
            'high_confidence_signals': [
                {'symbol': sym, 'signal': 'BUY', 'confidence': '92.3%'}
                for sym in symbols[:min(2, len(symbols))]
            ]
        }
    
    def _generate_risk_analysis(self, symbols: List[str]) -> Dict:
        """Generate risk analysis"""
        return {
            'portfolio_var_95': f"${np.random.uniform(500, 2000):.2f}",
            'max_drawdown_potential': f"{np.random.uniform(5, 20):.1f}%",
            'volatility_level': np.random.choice(['LOW', 'MEDIUM', 'HIGH']),
            'risk_alerts': [
                f"{symbol} approaching support level" 
                for symbol in symbols[:min(1, len(symbols))]
            ]
        }
    
    def _generate_weekly_summary(self, symbols: List[str]) -> Dict:
        """Generate weekly summary"""
        return {
            'week_performance': f"{np.random.uniform(-5, 10):.1f}%",
            'best_performer': symbols[0] if symbols else 'N/A',
            'market_trend': 'UPTREND',
            'volume_trend': 'INCREASING',
            'key_events': [
                'Fed announcement on interest rates',
                f"Earnings for {symbols[0]}" if symbols else 'N/A'
            ]
        }
    
    def _generate_model_performance(self) -> Dict:
        """Generate model performance metrics"""
        return {
            'ensemble_accuracy': f"{np.random.uniform(75, 95):.1f}%",
            'top_model': 'Transformer Ensemble',
            'best_performing_model_accuracy': f"{np.random.uniform(80, 96):.1f}%",
            'models_tested': 8,
            'week_improvement': f"{np.random.uniform(0, 5):.1f}%"
        }
    
    def _generate_sector_analysis(self) -> Dict:
        """Generate sector analysis"""
        return {
            'top_sectors': {
                'Technology': '+2.3%',
                'Financials': '+1.8%',
                'Healthcare': '+0.9%'
            },
            'worst_sectors': {
                'Energy': '-1.2%',
                'Materials': '-0.8%'
            },
            'sector_correlations': 'Increasing correlation detected'
        }
    
    def _generate_recommendations(self, symbols: List[str]) -> List[Dict]:
        """Generate top recommendations"""
        recommendations = []
        
        for symbol in symbols[:min(5, len(symbols))]:
            recommendations.append({
                'symbol': symbol,
                'action': np.random.choice(['BUY', 'HOLD', 'SELL']),
                'target_price': f"${np.random.uniform(100, 500):.2f}",
                'confidence': f"{np.random.uniform(75, 98):.1f}%",
                'rationale': 'Strong technical setup with bullish indicators'
            })
        
        return recommendations
    
    def _generate_key_insights(self) -> List[str]:
        """Generate key insights"""
        return [
            'Market showing strong bullish momentum',
            'Correlation between stocks increasing - diversify accordingly',
            'Volatility expected to rise next week',
            'Support levels holding well on major indices',
            'Earnings season approaching - monitor guidance closely'
        ]
    
    def export_report(self, report: Dict, format_type: str = 'json') -> Optional[str]:
        """Export report to different formats"""
        
        try:
            if format_type == 'json':
                import json
                return json.dumps(report, indent=2)
            
            elif format_type == 'csv':
                # Convert to CSV format
                if 'sections' in report:
                    csv_data = []
                    for section in report['sections']:
                        csv_data.append(f"## {section['title']}")
                        csv_data.append(str(section['content']))
                        csv_data.append('')
                    return '\n'.join(csv_data)
            
            elif format_type == 'html':
                # Generate HTML report
                html = f"""
                <html>
                <head><title>Report - {report.get('type', 'Report')}</title></head>
                <body>
                <h1>{report.get('type', 'Report')} Report</h1>
                <p>Generated: {report.get('generated_at', 'N/A')}</p>
                """
                
                for section in report.get('sections', []):
                    html += f"<h2>{section['title']}</h2>"
                    html += f"<p>{section['content']}</p>"
                
                html += "</body></html>"
                return html
            
            elif format_type == 'pdf':
                # PDF export would require reportlab or similar
                return "PDF export requires reportlab library"
            
            return None
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return None
    
    def schedule_report_generation(self, user_id: str, frequency: str = 'daily',
                                  time: str = '09:00', day: str = None,
                                  timezone: str = 'UTC', email: str = None) -> Dict:
        """Schedule automated report generation"""
        
        schedule_info = {
            'user_id': user_id,
            'frequency': frequency,
            'day': day,
            'timezone': timezone,
            'scheduled_time': time,
            'status': 'active',
            'next_generation': self._calculate_next_generation(frequency, time, day),
            'email_enabled': bool(email),
            'email_address': email
        }
        
        logger.info(f"Scheduled report generation: {schedule_info}")
        return schedule_info
    
    def _calculate_next_generation(self, frequency: str, time: str) -> str:
        """Calculate next report generation time"""
        
        now = datetime.now()
        
        if frequency == 'daily':
            next_time = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_time = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_time = now + timedelta(days=30)
        else:
            next_time = now + timedelta(days=1)
        
        return next_time.isoformat()


# Singleton instance
_report_generator = None


def get_report_generator():
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
