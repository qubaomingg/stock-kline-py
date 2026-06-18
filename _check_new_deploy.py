import httpx, json, time
base = "https://prefect.lanren.site/api"

# 等几秒让 worker 启动完成
print("等待 Prefect worker 完成 deployment 注册...")
time.sleep(5)

r = httpx.post(f"{base}/deployments/filter", json={"limit": 5}, timeout=10)
items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])

print(f"\n共 {len(items)} 个 deployment:")
for d in items:
    schedules = d.get("schedules", [])
    print(f"\n  name={d['name']}, id={d['id']}")
    print(f"  schedules (count={len(schedules)}):")
    for s in schedules:
        inner = s.get("schedule", {})
        print(f"    - active={s.get('active')}, cron={inner.get('cron')}, tz={inner.get('timezone')}")
if not items:
    print("  (空 - 可能还在创建中)")
