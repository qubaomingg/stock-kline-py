from service.main_force.main_force import get_main_force_analysis
import json

print("Testing A share:")
res_a = get_main_force_analysis("sz000001")
print(json.dumps(res_a, ensure_ascii=False, indent=2))

print("\nTesting HK share:")
res_hk = get_main_force_analysis("hk00700")
print(json.dumps(res_hk, ensure_ascii=False, indent=2))

print("\nTesting US share:")
res_us = get_main_force_analysis("AAPL")
print(json.dumps(res_us, ensure_ascii=False, indent=2))
