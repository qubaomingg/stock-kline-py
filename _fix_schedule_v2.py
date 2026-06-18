import httpx, json

base = "https://prefect.lanren.site"

# 正确格式：schedules (复数数组)，每个包含 schedule+CronSchedule
patch_data = {
    "schedules": [
        {
            "active": True,
            "schedule": {
                "cron": "0 0 * * *",
                "timezone": "Asia/Shanghai",
                "day_or": True
            },
            "max_scheduled_runs": 100
        }
    ]
}

print("PATCH data:")
print(json.dumps(patch_data, indent=2))

# 找到 deployment id
r = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
dep = next((d for d in items if d.get("name") == "lanren-daily-scheduler"), None)

if not dep:
    print("❌ 找不到 lanren-daily-scheduler")
    exit(1)

dep_id = dep["id"]
print(f"\nDeployment ID: {dep_id}")

# PATCH
patch_r = httpx.patch(
    f"{base}/api/deployments/{dep_id}",
    json=patch_data,
    timeout=10,
    headers={"Content-Type": "application/json"}
)
print(f"\nPATCH status: {patch_r.status_code}")
if patch_r.status_code == 200:
    print("✓ PATCH 成功")
    
    # 验证
    print("\n=== 验证 ===")
    r2 = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
    items2 = r2.json() if isinstance(r2.json(), list) else r2.json().get("items", [])
    for d2 in items2:
        if d2.get("id") == dep_id:
            schedules = d2.get("schedules", [])
            print(f"  deployment_name: {d2.get('name')}")
            print(f"  schedules: {json.dumps(schedules, indent=4)}")
            if schedules:
                s = schedules[0]
                print(f"  ✓ schedule 已设置:")
                print(f"    active={s.get('active')}")
                print(f"    cron={s.get('schedule', {}).get('cron')}")
                print(f"    timezone={s.get('schedule', {}).get('timezone')}")
            else:
                print(f"  ⚠  schedules 仍为空")
            break
else:
    print(f"❌ PATCH 失败: {patch_r.text}")

# 测试手动触发一次 flow run
print(f"\n=== 手动触发一次 flow run ===")
trigger_r = httpx.post(
    f"{base}/api/deployments/{dep_id}/create_flow_run",
    json={"name": "manual-test-run", "state": {"type": "SCHEDULED", "name": "Scheduled"}},
    timeout=10,
    headers={"Content-Type": "application/json"}
)
print(f"  status: {trigger_r.status_code}")
if trigger_r.status_code == 201:
    data = trigger_r.json()
    print(f"  ✓ flow_run created: id={data.get('id')}")
else:
    print(f"  response: {trigger_r.text[:500]}")
