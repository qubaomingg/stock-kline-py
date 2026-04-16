import akshare as ak
import traceback

print("Testing akshare for main force data...")

try:
    print("\n--- Fund Flow (stock_individual_fund_flow) ---")
    flow = ak.stock_individual_fund_flow(stock="000001", market="sz")
    print(flow.tail(2))
except Exception as e:
    print("Error:", e)
    traceback.print_exc()

try:
    print("\n--- Shareholders (stock_zh_a_gdhs) ---")
    gdhs = ak.stock_zh_a_gdhs_detail_em(symbol="000001")
    print(gdhs.head(2))
except Exception as e:
    print("Error:", e)
    # try another
    try:
        gdhs2 = ak.stock_zh_a_gdhs(symbol="000001")
        print(gdhs2.head(2))
    except Exception as e2:
        print("Error2:", e2)

