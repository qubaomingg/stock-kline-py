import httpx, json

base = "https://prefect.lanren.site"

# 先看当前 deployment 的完整数据
print("=== 当前 deployment 完整数据 ===")
r = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
items = r.json() if isinstance(r.json(), list) else (r.json().get("items") or r.json().get("results", []))
for d in items:
    print(f"  name={d.get('name')}")
    print(f"  schedule={json.dumps(d.get('schedule'), indent=4)}")
    print()

# 测试创建一个带 schedule 的 deployment
print("\n=== 测试 schedule 格式 ===")
# Prefect 3.x schedule format
schedule_dict = {
    "cron": "0 0 * * *",
    "timezone": "Asia/Shanghai",
    "day_or": True,
}

print(f"测试用 schedule: {json.dumps(schedule_dict)}")

# 尝试直接用 API 创建一个测试 deployment 来验证格式
# 需要先有一个 flow，用已有的 daily-scheduler flow
for d in items:
    if d.get("name") == "lanren-daily-scheduler":
        dep_id = d.get("id")
        print(f"\n找到 deployment: {dep_id}")
        
        # PATCH 这个 deployment，更新 schedule
        patch_data = {
            "schedule": schedule_dict
        }
        print(f"PATCH data: {json.dumps(patch_data, indent=2)}")
        
        patch_r = httpx.patch(
            f"{base}/api/deployments/{dep_id}",
            json=patch_data,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        print(f"PATCH status: {patch_r.status_code}")
        print(f"PATCH response: {patch_r.text[:500]}")
        
        if patch_r.status_code == 200:
            print("\n✓ PATCH 成功，重新查询验证:")
            r2 = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
            items2 = r2.json() if isinstance(r2.json(), list) else (r2.json().get("items") or r2.json().get("results", []))
            for d2 in items2:
                if d2.get("id") == dep_id:
                    print(f"  schedule={json.dumps(d2.get('schedule'), indent=4)}")
        break
