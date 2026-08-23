from StockSageAI.stocks_database import get_stocks_database

if __name__ == '__main__':
    db = get_stocks_database()
    us = db.get_all_stocks('us')
    india = db.get_all_stocks('india')
    print('US count:', len(us))
    print('India count:', len(india))
    # Sample some entries
    print('First 5 US:', us[:5])
    print('First 5 India:', india[:5])

    # Try fetching info for a known ticker
    info = db.get_stock_info('AAPL')
    if info:
        print('AAPL name:', info.get('name'))
        print('AAPL price (may be 0 if unavailable):', info.get('price'))
    else:
        print('AAPL info: None')
