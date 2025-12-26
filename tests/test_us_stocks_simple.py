#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from service.stocks.us.us_stocks import get_us_stocks

print("Testing get_us_stocks function...")
print("ALPHA_VANTAGE_API_KEY exists:", os.getenv('ALPHA_VANTAGE_API_KEY') is not None)

# 设置超时
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Function timed out after 60 seconds")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60秒超时

try:
    result = get_us_stocks()
    print("\nFunction completed successfully!")
    print("Success:", result.get('success', False))
    print("Count:", result.get('count', 0))
    print("Source:", result.get('source', 'unknown'))
    print("Timestamp:", result.get('timestamp', 'unknown'))
    
    # 显示前几个股票
    stocks = result.get('stocks', [])
    if stocks:
        print(f"\nFirst {min(3, len(stocks))} stocks:")
        for i, stock in enumerate(stocks[:3]):
            print(f"  {i+1}. {stock.get('code', 'N/A')}: {stock.get('name', 'N/A')}")
    else:
        print("\nNo stocks returned")
        
except TimeoutError as e:
    print(f"\nError: {e}")
    print("The function is taking too long. This might be due to:")
    print("1. Alpha Vantage API rate limiting (free tier has 5 calls/minute)")
    print("2. Network connectivity issues")
    print("3. API response delays")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    signal.alarm(0)  # 取消超时
    print("\nTest completed.")