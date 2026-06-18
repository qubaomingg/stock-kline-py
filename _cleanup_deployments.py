import httpx, json, sys

base = "https://prefect.lanren.site/api"

# 1. 列出所有 deployment
r = httpx.post(f"{base}/deployments/filter", json={"limit": 20}, timeout=10)
items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])

print("=== 删除旧 deployment ===")
for d in items:
    if "daily" in d.get("name", "").lower():
        dep_id = d["id"]
        print(f"  删除 {d['name']} ({dep_id})")
        del_r = httpx.delete(f"{base}/deployments/{dep_id}", timeout=10)
        print(f"    status: {del_r.status_code}")

# 2. 删除 flow
print("\n=== 删除旧 flow ===")
r2 = httpx.post(f"{base}/flows/filter", json={"limit": 10}, timeout=10)
flows = r2.json() if isinstance(r2.json(), list) else r2.json().get("items", [])
for f in flows:
    if "daily" in f.get("name", "").lower():
        print(f"  删除 flow: {f['name']} ({f['id']})")
        del_r = httpx.delete(f"{base}/flows/{f['id']}", timeout=10)
        print(f"    status: {del_r.status_code}")

print("\n✅ 清理完成，重启 PM2 worker 后会重新创建带 schedule 的 deployment")
