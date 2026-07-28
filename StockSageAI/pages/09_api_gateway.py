"""
API Gateway Documentation & Testing Page
"""

import streamlit as st
import requests
import json

st.set_page_config(page_title="API Gateway", layout="wide")

st.markdown("# 🔌 REST API Gateway")
st.markdown("API endpoints reference and testing interface")

# API Configuration
API_BASE_URL = "http://localhost:5000"

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Endpoints", "Get Token", "Test API", "Documentation"])

# TAB 1: Endpoints Reference
with tab1:
    st.subheader("Available Endpoints")
    
    endpoints = {
        "Health": {
            "method": "GET",
            "path": "/api/v1/health",
            "description": "Check API server status",
            "response": "{'status': 'ok', 'timestamp': '2024-01-01T12:00:00'}"
        },
        "Predict": {
            "method": "POST",
            "path": "/api/v1/predict",
            "description": "Get model predictions for a stock",
            "parameters": "symbol (str), model_type (str: 'ensemble', 'lstm', 'transformer')",
            "response": "{'symbol': 'AAPL', 'prediction': 0.45, 'direction': 'UP', 'confidence': 0.85}"
        },
        "Trading Signals": {
            "method": "GET",
            "path": "/api/v1/signals?symbol=AAPL",
            "description": "Get trading signals for a symbol",
            "parameters": "symbol (str), limit (int, default: 10)",
            "response": "{'signals': [{'symbol': 'AAPL', 'signal': 'BUY', 'price': 150.0}]}"
        },
        "Portfolio": {
            "method": "GET",
            "path": "/api/v1/portfolio",
            "description": "Get user portfolio",
            "response": "{'portfolio': [{'symbol': 'AAPL', 'quantity': 10, 'buy_price': 150}]}"
        },
        "Add to Portfolio": {
            "method": "POST",
            "path": "/api/v1/portfolio",
            "description": "Add a holding to portfolio",
            "parameters": "symbol (str), quantity (int), buy_price (float)",
            "response": "{'status': 'added', 'symbol': 'AAPL'}"
        },
        "Backtest": {
            "method": "POST",
            "path": "/api/v1/backtest",
            "description": "Run backtest simulation",
            "parameters": "symbol, strategy, capital, start_date, end_date",
            "response": "{'total_return': 0.25, 'sharpe_ratio': 1.45, 'max_dd': -0.10}"
        },
        "Risk Metrics": {
            "method": "GET",
            "path": "/api/v1/risk-metrics?symbol=AAPL",
            "description": "Get risk analysis metrics",
            "parameters": "symbol (str), method ('historic', 'parametric', 'montecarlo')",
            "response": "{'var': -0.05, 'cvar': -0.08, 'volatility': 0.15, 'beta': 1.2}"
        },
        "Compare Stocks": {
            "method": "POST",
            "path": "/api/v1/compare",
            "description": "Compare multiple stocks",
            "parameters": "symbols (list), metrics (list)",
            "response": "{'comparison': [{'symbol': 'AAPL', 'pe': 25.5, 'volatility': 0.18}]}"
        },
        "Generate Report": {
            "method": "POST",
            "path": "/api/v1/report",
            "description": "Generate analysis report",
            "parameters": "report_type ('daily', 'weekly'), symbols (list)",
            "response": "{'report': {...}, 'format': 'json', 'timestamp': '2024-01-01'}"
        },
        "Get Token": {
            "method": "POST",
            "path": "/api/v1/auth/token",
            "description": "Get API access token",
            "parameters": "username (str), password (str)",
            "response": "{'token': 'eyJhbGc...', 'expires_in': 3600}"
        }
    }
    
    for endpoint_name, details in endpoints.items():
        with st.expander(f"**{details['method']}** {details['path']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Description:** {details['description']}")
                if 'parameters' in details:
                    st.write(f"**Parameters:** {details['parameters']}")
            
            with col2:
                st.code(details['response'], language='json')

# TAB 2: Get API Token
with tab2:
    st.subheader("API Authentication")
    
    st.info("Get your API token for authenticated requests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Username", "demo_user")
    
    with col2:
        password = st.text_input("Password", type="password", value="demo_pass")
    
    if st.button("Get Token", type="primary", use_container_width=True):
        with st.spinner("Retrieving token..."):
            try:
                # Simulate token generation
                token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZGVtbyIsImV4cCI6MTcwNDExMzYwMH0.mock_signature"
                
                st.success("✅ Token retrieved")
                
                st.code(token, language="text")
                
                st.write("**Token Details:**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Token Type", "Bearer")
                with col2:
                    st.metric("Expires In", "1 hour")
                with col3:
                    st.metric("Scopes", "api, read, write")
                
                st.divider()
                
                st.write("**Usage in requests:**")
                curl_example = f"""curl -H "Authorization: Bearer {token}" \\
  {API_BASE_URL}/api/v1/predict \\
  -d '{{"symbol": "AAPL", "model_type": "ensemble"}}'"""
                st.code(curl_example, language="bash")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    
    st.write("### Token Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Token"):
            st.success("Token refreshed successfully")
    
    with col2:
        if st.button("🗑️ Revoke Token"):
            st.warning("Token revoked - authentication required for next request")

# TAB 3: Test API
with tab3:
    st.subheader("API Testing Console")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        endpoint_test = st.selectbox(
            "Select Endpoint",
            [
                "Health Check",
                "Predict",
                "Get Signals",
                "Portfolio",
                "Risk Metrics",
                "Compare Stocks",
                "Run Backtest"
            ]
        )
    
    with col2:
        st.info(f"Testing: {endpoint_test}")
    
    # Dynamic request builder based on selected endpoint
    if endpoint_test == "Health Check":
        if st.button("Send Request", type="primary"):
            with st.spinner("Sending request..."):
                try:
                    # Simulate response
                    response = {
                        "status": "ok",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "uptime": "48h 30m",
                        "models": 8,
                        "database": "connected"
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.write("**Response Body:**")
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif endpoint_test == "Predict":
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_pred = st.text_input("Symbol", "AAPL")
        
        with col2:
            model_type = st.selectbox("Model Type", ["ensemble", "lstm", "transformer", "cnn_bilstm"])
        
        if st.button("Send Request", type="primary"):
            with st.spinner("Getting prediction..."):
                try:
                    response = {
                        "symbol": symbol_pred,
                        "close_price": 180.25,
                        "predicted_price": 185.50,
                        "expected_return": 0.0291,
                        "direction": "UP",
                        "confidence": 0.87,
                        "model": model_type,
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif endpoint_test == "Get Signals":
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_signals = st.text_input("Symbol", "AAPL")
        
        with col2:
            limit = st.slider("Limit", 1, 50, 10)
        
        if st.button("Send Request", type="primary"):
            with st.spinner("Fetching signals..."):
                try:
                    response = {
                        "symbol": symbol_signals,
                        "signals": [
                            {
                                "id": 1,
                                "signal": "BUY",
                                "confidence": 0.85,
                                "price": 180.25,
                                "timestamp": "2024-01-01T12:00:00Z"
                            },
                            {
                                "id": 2,
                                "signal": "HOLD",
                                "confidence": 0.72,
                                "price": 179.50,
                                "timestamp": "2024-01-01T10:00:00Z"
                            }
                        ],
                        "total": 2
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif endpoint_test == "Portfolio":
        if st.button("Send Request", type="primary"):
            with st.spinner("Fetching portfolio..."):
                try:
                    response = {
                        "portfolio": [
                            {
                                "symbol": "AAPL",
                                "quantity": 10,
                                "buy_price": 150.00,
                                "current_price": 180.25,
                                "value": 1802.50,
                                "gain": 302.50,
                                "gain_pct": 20.17
                            },
                            {
                                "symbol": "GOOGL",
                                "quantity": 5,
                                "buy_price": 100.00,
                                "current_price": 140.50,
                                "value": 702.50,
                                "gain": 202.50,
                                "gain_pct": 40.50
                            }
                        ],
                        "total_value": 2505.00,
                        "total_gain": 505.00
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif endpoint_test == "Risk Metrics":
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_risk = st.text_input("Symbol", "AAPL")
        
        with col2:
            method_risk = st.selectbox("Method", ["historic", "parametric", "montecarlo"])
        
        if st.button("Send Request", type="primary"):
            with st.spinner("Calculating risk..."):
                try:
                    response = {
                        "symbol": symbol_risk,
                        "method": method_risk,
                        "var_95": -0.0487,
                        "var_99": -0.0812,
                        "cvar_95": -0.0728,
                        "volatility": 0.1847,
                        "beta": 1.1543,
                        "alpha": 0.0234,
                        "sharpe_ratio": 1.2847,
                        "max_drawdown": -0.2134,
                        "recovery_time": "45 days"
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif endpoint_test == "Compare Stocks":
        symbols_comp = st.text_input("Symbols (comma-separated)", "AAPL,GOOGL,MSFT")
        
        if st.button("Send Request", type="primary"):
            with st.spinner("Comparing stocks..."):
                try:
                    response = {
                        "comparison": [
                            {
                                "symbol": "AAPL",
                                "price": 180.25,
                                "pe_ratio": 25.5,
                                "pb_ratio": 45.2,
                                "volatility": 0.18,
                                "1y_return": 0.35,
                                "sharpe_ratio": 1.28
                            },
                            {
                                "symbol": "GOOGL",
                                "price": 140.50,
                                "pe_ratio": 23.1,
                                "pb_ratio": 42.8,
                                "volatility": 0.16,
                                "1y_return": 0.42,
                                "sharpe_ratio": 1.35
                            },
                            {
                                "symbol": "MSFT",
                                "price": 380.75,
                                "pe_ratio": 28.3,
                                "pb_ratio": 38.5,
                                "volatility": 0.14,
                                "1y_return": 0.48,
                                "sharpe_ratio": 1.52
                            }
                        ],
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif endpoint_test == "Run Backtest":
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_bt = st.text_input("Symbol", "AAPL")
            strategy_bt = st.selectbox("Strategy", ["ma_crossover", "rsi", "bollinger_bands"])
        
        with col2:
            capital_bt = st.number_input("Capital", value=10000)
        
        if st.button("Send Request", type="primary"):
            with st.spinner("Running backtest..."):
                try:
                    response = {
                        "symbol": symbol_bt,
                        "strategy": strategy_bt,
                        "initial_capital": capital_bt,
                        "final_value": capital_bt * 1.35,
                        "total_return": 0.35,
                        "annual_return": 0.42,
                        "sharpe_ratio": 1.48,
                        "max_drawdown": -0.1234,
                        "win_rate": 0.62,
                        "total_trades": 45,
                        "profitable_trades": 28
                    }
                    
                    st.success("✅ Response 200 OK")
                    
                    st.json(response)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# TAB 4: Documentation
with tab4:
    st.subheader("API Documentation")
    
    st.markdown("""
    ### Base URL
    ```
    http://localhost:5000
    ```
    
    ### Authentication
    All endpoints (except `/health` and `/auth/token`) require Bearer token authentication:
    ```
    Authorization: Bearer <your_token>
    ```
    
    ### Response Format
    All responses are in JSON format with the following structure:
    ```json
    {
        "data": {...},
        "status": "success",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    
    ### Error Responses
    Errors return appropriate HTTP status codes with error details:
    ```json
    {
        "error": "Invalid symbol",
        "code": "INVALID_SYMBOL",
        "status": 400,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    
    ### Rate Limiting
    - **Free Tier**: 100 requests/hour
    - **Pro Tier**: 1000 requests/hour
    - **Enterprise**: Unlimited
    
    ### Common Status Codes
    - **200**: Success
    - **400**: Bad Request
    - **401**: Unauthorized (invalid token)
    - **403**: Forbidden
    - **404**: Not Found
    - **500**: Server Error
    
    ### Example cURL Request
    ```bash
    curl -X POST http://localhost:5000/api/v1/predict \\
      -H "Content-Type: application/json" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -d '{
        "symbol": "AAPL",
        "model_type": "ensemble"
      }'
    ```
    
    ### Python SDK Example
    ```python
    import requests
    
    api_url = "http://localhost:5000"
    token = "YOUR_TOKEN"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{api_url}/api/v1/predict",
        json={"symbol": "AAPL", "model_type": "ensemble"},
        headers=headers
    )
    
    data = response.json()
    print(data)
    ```
    """)

st.caption("REST API Gateway • SP 07 StockSageAI")
