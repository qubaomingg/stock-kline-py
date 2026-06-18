import httpx, json

base = "https://prefect.lanren.site"

patch_data = {
    "schedules": [
        {
            "active": True,
            "schedule": {
                "cron": "0 0 * * *",
                "timezone": "Asia/Shanghai",
                "day_or": True
            },
            "max_scheduled_runs": 50
        }
    ]
}

# 找到 deployment
r = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
dep = next((d for d in items if d.get("name") == "lanren-daily-scheduler"), None)

if not dep:
    print("❌ 找不到 lanren-daily-scheduler")
    exit(1)

dep_id = dep["id"]
print(f"Deployment ID: {dep_id}")

# PATCH
patch_r = httpx.patch(
    f"{base}/api/deployments/{dep_id}",
    json=patch_data,
    timeout=10,
    headers={"Content-Type": "application/json"}
)
print(f"PATCH status: {patch_r.status_code}")
if patch_r.status_code == 200:
    print("✓ PATCH 成功")
    
    # 验证
    r2 = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
    items2 = r2.json() if isinstance(r2.json(), list) else r2.json().get("items", [])
    for d2 in items2:
        if d2.get("id") == dep_id:
            schedules = d2.get("schedules", [])
            print(f"\n=== 验证 ===")
            print(f"  name: {d2.get('name')}")
            print(f"  schedules: {json.dumps(schedules, indent=4)}")
            
            # 触发一次 schedule 计算，确保有 scheduled runs
            print(f"\n=== 生成 scheduled runs ===")
            trigger_r = httpx.post(
                f"{base}/api/deployments/{dep_id}/schedule",
                json={"max_runs": 5},
                timeout=10
            )
            print(f"  status: {trigger_r.status_code}")
            if trigger_r.status_code == 200:
                data = trigger_r.json()
                if isinstance(data, dict):
                    count = data.get("count", data.get("total", "N/A"))
                    print(f"  已生成 {count} 个 scheduled runs")
                else:
                    print(f"  response: {str(data)[:200]}")
            
            print(f"\n✅ 完成！在 UI 访问:")
            print(f"   https://prefect.lanren.site/deployments/deployment/{dep_id}")
            break
else:
    print(f"❌ PATCH 失败: {patch_r.text}")
