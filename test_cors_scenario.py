import requests

url = "https://stock-kline-py-production.up.railway.app/api/stock/baseinfo?code=600519"

# 1. 模拟旧版本 request.js 的行为 (带着 Cookie 和 credentials: include 的概念，导致浏览器发起 OPTIONS 时要求 allow-credentials)
# 这里用 requests 库模拟浏览器的 OPTIONS 预检请求行为
print("=== Scenario 1: Old request.js behavior (with custom Cookie header or credentials) ===")
# 浏览器在带 credentials 时发出的 OPTIONS 请求
headers_old = {
    "Origin": "https://lanren.site",
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "content-type, cookie" # 如果前端手动设置了 cookie，预检会带上这个
}
try:
    res1 = requests.options(url, headers=headers_old)
    print(f"Status: {res1.status_code}")
    print(f"CORS Headers: {res1.headers.get('access-control-allow-origin')}")
    # 后端如果配置 allow_origins=["*"] 且 allow_credentials=True，在真实浏览器中其实是不被允许的
    # FastAPI 会自动把 allow_origin 设置为具体的 Origin 来配合 credentials
except Exception as e:
    print(f"Error: {e}")

print("\n=== Scenario 2: New request.js behavior (no custom Cookie, omit credentials) ===")
# 浏览器在不带 credentials (omit) 时发出的纯净 OPTIONS 请求
headers_new = {
    "Origin": "https://lanren.site",
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "content-type" 
}
try:
    res2 = requests.options(url, headers=headers_new)
    print(f"Status: {res2.status_code}")
    print(f"CORS Headers: {res2.headers.get('access-control-allow-origin')}")
except Exception as e:
    print(f"Error: {e}")

