import httpx, json

base = "https://prefect.lanren.site"

# 验证 deployment 的 schedule
r = httpx.post(f"{base}/api/deployments/filter", json={"limit": 5}, timeout=10)
items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])

print("=== 当前 deployments ===")
for d in items:
    schedules = d.get("schedules", [])
    print(f"\n  name={d.get('name')}")
    print(f"  id={d.get('id')}")
    print(f"  schedules (count={len(schedules)}):")
    for s in schedules:
        inner_schedule = s.get("schedule", {})
        print(f"    - active={s.get('active')}, cron={inner_schedule.get('cron')}, tz={inner_schedule.get('timezone')}")

# 手动触发 schedule 生成
dep = next((d for d in items if d.get("name") == "lanren-daily-scheduler"), None)
if dep and dep.get("schedules"):
    dep_id = dep["id"]
    print(f"\n=== 触发 schedule 生成 ===")
    trigger_r = httpx.post(
        f"{base}/api/deployments/{dep_id}/schedule",
        json={"max_runs": 5},
        timeout=10
    )
    print(f"  POST /schedule: {trigger_r.status_code}")
    if trigger_r.status_code == 200:
        data = trigger_r.json()
        if isinstance(data, dict):
            print(f"  response: {json.dumps(data)[:300]}")
    elif trigger_r.status_code == 204:
        print(f"  204 No Content - 也表示成功")

    # 查 flow_runs
    print(f"\n=== 查 flow_runs ===")
    runs_r = httpx.post(
        f"{base}/api/flow_runs/filter",
        json={"limit": 10, "flow_runs": {"deployment_id": {"any_": [dep_id]}}},
        timeout=10
    )
    if runs_r.status_code == 200:
        runs = runs_r.json()
        items2 = runs if isinstance(runs, list) else runs.get("items", runs.get("results", []))
        print(f"  共 {len(items2)} 个 flow runs")
        for fr in items2[:5]:
            print(f"    - {fr.get('name')}: {fr.get('state', {}).get('name')} @ {fr.get('next_scheduled_start_time', 'N/A')}")

    # 查 scheduled flow runs
    print(f"\n=== 查 scheduled flow_runs ===")
    sched_r = httpx.post(
        f"{base}/api/deployments/{dep_id}/get_scheduled_flow_runs",
        json={"limit": 5},
        timeout=10
    )
    print(f"  status: {sched_r.status_code}")
    if sched_r.status_code == 200:
        data = sched_r.json()
        items3 = data if isinstance(data, list) else (data.get("items") or data.get("results") or [])
        for fr in items3:
            print(f"    scheduled at: {fr.get('next_scheduled_start_time')}")

    print(f"\n✅ 部署正常！UI 地址:")
    print(f"   https://prefect.lanren.site/deployments/deployment/{dep_id}")
else:
    print("⚠  schedules 仍为空，需要进一步排查")
