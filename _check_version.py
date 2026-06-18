import httpx, json

base = "https://prefect.lanren.site"

# 1. 检查健康接口和版本信息
print("=== 健康检查 ===")
for path in ["/api/health", "/health", "/docs", "/openapi.json"]:
    try:
        r = httpx.get(f"{base}{path}", timeout=10)
        print(f"  {path}: {r.status_code}")
        if r.status_code == 200 and path.endswith(".json"):
            # Try to find version in openapi
            data = r.json()
            version = data.get("info", {}).get("version", "unknown")
            print(f"    version: {version}")
            print(f"    title: {data.get('info', {}).get('title', 'N/A')}")
    except Exception as e:
        print(f"  {path}: ERROR - {e}")

# 2. 检查 Prefect 3.x 专用 API 端点
print("\n=== Prefect 3.x API 测试 ===")
for path in ["/api/deployments/filter", "/api/deployments/query"]:
    try:
        r = httpx.post(f"{base}{path}", json={}, timeout=10)
        print(f"  POST {path}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("items", data.get("results", []))
            print(f"    items: {len(items)}")
    except Exception as e:
        print(f"  POST {path}: ERROR - {e}")

# 3. 检查 Prefect 2.x API 端点
print("\n=== Prefect 2.x API 测试 ===")
for path in ["/deployments", "/api/deployments"]:
    try:
        r = httpx.get(f"{base}{path}", timeout=10)
        print(f"  GET {path}: {r.status_code}")
        if r.status_code == 200:
            text = r.text[:300]
            print(f"    response: {text}")
    except Exception as e:
        print(f"  GET {path}: ERROR - {e}")

# 4. 检查 flows
print("\n=== Flows 测试 ===")
for path in ["/api/flows/filter", "/api/flows", "/flows"]:
    try:
        if "filter" in path:
            r = httpx.post(f"{base}{path}", json={}, timeout=10)
        else:
            r = httpx.get(f"{base}{path}", timeout=10)
        print(f"  {path}: {r.status_code}")
        if r.status_code == 200:
            text = r.text[:300]
            print(f"    response: {text}")
    except Exception as e:
        print(f"  {path}: ERROR - {e}")
