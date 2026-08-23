"""
Report Generator Page
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

from StockSageAI.report_generator import get_report_generator

st.set_page_config(page_title="Report Generator", layout="wide")

st.markdown("# 📊 Automated Report Generator")
st.markdown("Generate daily/weekly analysis reports with scheduling")

generator = get_report_generator()

# Tabs for different report functions
tab1, tab2, tab3 = st.tabs(["Generate Report", "Scheduling", "Report History"])

# TAB 1: Generate Report
with tab1:
    st.subheader("Generate Custom Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["daily", "weekly"],
            format_func=lambda x: x.title()
        )
    
    with col2:
        symbols = st.text_input(
            "Symbols (comma-separated, e.g., AAPL, GOOGL, MSFT)",
            "AAPL,GOOGL"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format",
            ["json", "csv", "html"],
            format_func=lambda x: x.upper()
        )
    
    with col2:
        st.info(f"Report Type: {report_type.upper()}")
    
    if st.button("Generate Report", type="primary"):
        with st.spinner(f"Generating {report_type} report..."):
            try:
                symbol_list = [s.strip().upper() for s in symbols.split(",")]
                
                # Generate report
                user_id = None
                if st.session_state.get('user'):
                    user_id = st.session_state.user.get('id') or st.session_state.user.get('username')

                report = generator.generate_report(
                    report_type=report_type,
                    user_id=user_id,
                    symbols=symbol_list,
                    export_format=export_format
                )
                
                if report:
                    st.success(f"✅ {report_type.title()} report generated")
                    
                    # Display report sections based on type
                    if report_type == "daily":
                        st.write("### Executive Summary")
                        if report.get('summary'):
                            st.write(report['summary'])
                        
                        st.write("### Market Overview")
                        if report.get('market_overview'):
                            overview_df = pd.DataFrame([report['market_overview']])
                            st.dataframe(overview_df)
                        
                        st.write("### Stock Analysis")
                        if report.get('stock_analysis'):
                            analysis_df = pd.DataFrame(report['stock_analysis'])
                            st.dataframe(analysis_df)
                        
                        st.write("### Portfolio Status")
                        if report.get('portfolio_status'):
                            status_df = pd.DataFrame([report['portfolio_status']])
                            st.dataframe(status_df)
                        
                        st.write("### Trading Signals")
                        if report.get('trading_signals'):
                            signals_df = pd.DataFrame(report['trading_signals'])
                            st.dataframe(signals_df)
                        
                        st.write("### Risk Analysis")
                        if report.get('risk_analysis'):
                            risk_df = pd.DataFrame([report['risk_analysis']])
                            st.dataframe(risk_df)
                    
                    else:  # weekly
                        st.write("### Weekly Performance Analysis")
                        if report.get('performance_analysis'):
                            perf_df = pd.DataFrame([report['performance_analysis']])
                            st.dataframe(perf_df)
                        
                        st.write("### Model Accuracy Report")
                        if report.get('model_accuracy'):
                            accuracy_df = pd.DataFrame([report['model_accuracy']])
                            st.dataframe(accuracy_df)
                        
                        st.write("### Sector Analysis")
                        if report.get('sector_analysis'):
                            sector_df = pd.DataFrame(report['sector_analysis'])
                            st.dataframe(sector_df)
                        
                        st.write("### Top Recommendations")
                        if report.get('recommendations'):
                            for i, rec in enumerate(report['recommendations'], 1):
                                st.write(f"{i}. {rec}")
                        
                        st.write("### Key Insights")
                        if report.get('key_insights'):
                            for insight in report['key_insights']:
                                st.write(f"• {insight}")
                    
                    st.divider()
                    
                    # Export options
                    st.write("### Export Report")
                    
                    if export_format == "json":
                        json_str = json.dumps(report, indent=2, default=str)
                        st.download_button(
                            label="📥 Download as JSON",
                            data=json_str,
                            file_name=f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
                        # Display code safely with proper truncation
                        preview_json = json_str[:500]
                        if len(json_str) > 500:
                            preview_json = preview_json + "\n\n... (report continues) ...\n}"
                        st.code(preview_json, language="json")
                    
                    elif export_format == "csv":
                        # Convert first section to CSV
                        if report_type == "daily" and report.get('stock_analysis'):
                            csv_data = pd.DataFrame(report['stock_analysis']).to_csv(index=False)
                        else:
                            csv_data = pd.DataFrame([report]).to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv_data,
                            file_name=f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                    else:  # html
                        html_content = f"""
                        <html>
                            <head>
                                <title>{report_type.title()} Report</title>
                                <style>
                                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                                    h2 {{ color: #0066cc; }}
                                    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                                    th {{ background-color: #0066cc; color: white; }}
                                </style>
                            </head>
                            <body>
                                <h1>{report_type.title()} Report</h1>
                                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                                <p>Report content would be rendered here</p>
                            </body>
                        </html>
                        """
                        
                        st.download_button(
                            label="📥 Download as HTML",
                            data=html_content,
                            file_name=f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.html",
                            mime="text/html"
                        )
                
                else:
                    st.error("Failed to generate report")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

# TAB 2: Scheduling
with tab2:
    st.subheader("Schedule Automated Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        schedule_type = st.selectbox(
            "Schedule Type",
            ["daily", "weekly"],
            key="schedule_type",
            format_func=lambda x: x.title()
        )
    
    with col2:
        report_type_sched = st.selectbox(
            "Report Type",
            ["daily", "weekly"],
            key="report_type_sched",
            format_func=lambda x: x.title()
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if schedule_type == "daily":
            time = st.time_input("Time", value=datetime.strptime("09:00", "%H:%M").time())
        else:
            day = st.selectbox(
                "Day",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            time = st.time_input("Time", value=datetime.strptime("09:00", "%H:%M").time())
    
    with col2:
        symbols_sched = st.text_input(
            "Symbols (comma-separated)",
            "AAPL,GOOGL,MSFT",
            key="symbols_sched"
        )
    
    with col3:
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "EST", "CST", "MST", "PST", "IST"],
            index=4
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_email = st.checkbox("Send via Email")
    
    with col2:
        if enable_email:
            email = st.text_input("Email Address")
    
    if st.button("Schedule Report", type="primary"):
        with st.spinner("Scheduling report..."):
            try:
                symbol_list = [s.strip().upper() for s in symbols_sched.split(",")]
                
                result = generator.schedule_report_generation(
                    user_id='demo_user',
                    frequency=report_type_sched,
                    time=time.strftime("%H:%M"),
                    day=day if schedule_type == 'weekly' else None,
                    timezone=timezone,
                    email=email if enable_email else None
                )
                
                if result:
                    st.success(f"✅ Report scheduled for {schedule_type} at {time}")
                    
                    st.info(f"""
                    **Schedule Details:**
                    - Type: {schedule_type.upper()}
                    - Report: {report_type_sched.upper()}
                    - Symbols: {', '.join(symbol_list)}
                    - Time: {time.strftime('%H:%M')} {timezone}
                    - Email Notification: {'Yes' if enable_email else 'No'}
                    """)
                
                else:
                    st.error("Failed to schedule report")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

# TAB 3: Report History
with tab3:
    st.subheader("Report History & Archives")
    
    col1, col2 = st.columns(2)
    
    with col1:
        filter_type = st.selectbox(
            "Filter by Type",
            ["all", "daily", "weekly"]
        )
    
    with col2:
        days_back = st.slider("Days Back", 1, 90, 30)
    
    # Mock history data
    history_data = []
    for i in range(10):
        date = datetime.now() - timedelta(days=i)
        history_data.append({
            'Date': date.strftime('%Y-%m-%d %H:%M'),
            'Type': 'Daily' if i % 2 == 0 else 'Weekly',
            'Symbols': 'AAPL, GOOGL, MSFT',
            'Status': '✅ Completed',
            'Format': 'JSON' if i % 3 == 0 else 'CSV',
            'File Size': f"{50 + i * 5} KB"
        })
    
    history_df = pd.DataFrame(history_data)
    
    if filter_type != "all":
        history_df = history_df[history_df['Type'].str.lower() == filter_type]
    
    st.dataframe(history_df)
    
    st.divider()
    
    st.write("### Action")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download Selected"):
            st.info("Select a report from history to download")
    
    with col2:
        if st.button("🔄 Regenerate"):
            st.success("Report regeneration started")
    
    with col3:
        if st.button("🗑️ Delete"):
            st.warning("Delete confirmation required")

st.caption("Report Generator • SP 07 StockSageAI")
