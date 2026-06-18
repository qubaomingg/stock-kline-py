import httpx, json

base = "https://prefect.lanren.site"

# 1. 查一下正确的 UI 路径
print("=== UI 路径探测 ===")
for path in ["/", "/deployments", "/flows", "/v2/"]:
    try:
        r = httpx.get(f"{base}{path}", timeout=10, follow_redirects=True)
        print(f"  {path}: status={r.status_code}, final_url={r.url}, title_contains_v2={'/v2/' in str(r.url)}")
    except Exception as e:
        print(f"  {path}: ERROR - {e}")

# 2. 查 deployment 详情
print("\n=== Deployment 详情 ===")
r = httpx.post(f"{base}/api/deployments/filter", json={"limit": 20}, timeout=10)
print(f"Status: {r.status_code}")
data = r.json()
items = data if isinstance(data, list) else data.get("items", data.get("results", []))
for d in items:
    print(f"  id: {d.get('id')}")
    print(f"  name: {d.get('name')}")
    print(f"  flow_id: {d.get('flow_id')}")
    print(f"  schedule: {json.dumps(d.get('schedule', {}))}")
    print(f"  entrypoint: {d.get('entrypoint')}")
    print(f"  work_pool_name: {d.get('work_pool_name')}")
    print()

# 3. 查 work pool
print("\n=== Work Pools ===")
r = httpx.post(f"{base}/api/work_pools/filter", json={}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data if isinstance(data, list) else data.get("items", [])
    for wp in items:
        print(f"  name={wp.get('name')}, type={wp.get('type')}, status={wp.get('status')}")
else:
    print("  无法获取 work pools")
