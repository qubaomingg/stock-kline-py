import httpx, json

base = "https://prefect.lanren.site"

# 1. 看 openapi schema 找 deployment 的正确字段名
print("=== 查看 openapi 中 deployment 相关 schema ===")
r = httpx.get(f"{base}/openapi.json", timeout=10)
spec = r.json()

# 找 deployments 的 PATCH/POST schema
paths = spec.get("paths", {})
for path, methods in paths.items():
    if "deployment" in path.lower():
        for method, details in methods.items():
            if method.upper() in ["POST", "PATCH", "PUT"]:
                # 看 requestBody
                body = details.get("requestBody", {})
                if body:
                    content = body.get("content", {})
                    for ct, schema_info in content.items():
                        schema_ref = schema_info.get("schema", {}).get("$ref", "")
                        if schema_ref:
                            schema_name = schema_ref.split("/")[-1]
                            # 解析 schema
                            defs = spec.get("components", {}).get("schemas", {})
                            s = defs.get(schema_name, {})
                            props = list(s.get("properties", {}).keys())
                            print(f"\n  {method.upper()} {path}")
                            print(f"    schema: {schema_name}")
                            print(f"    properties: {props}")
                            
                            # 特别找 schedule 相关
                            for prop_name, prop_val in s.get("properties", {}).items():
                                if "schedule" in prop_name.lower() or prop_name == "schedules":
                                    print(f"    ⭐ {prop_name}: {json.dumps(prop_val)[:200]}")

# 2. 直接查 deployment schema def
print("\n\n=== Deployment schemas ===")
defs = spec.get("components", {}).get("schemas", {})
for name in sorted(defs.keys()):
    if "deployment" in name.lower() and "create" in name.lower():
        s = defs[name]
        props = list(s.get("properties", {}).keys())
        print(f"\n  {name}:")
        print(f"    props: {props}")
        for prop_name, prop_val in s.get("properties", {}).items():
            if "schedule" in prop_name.lower():
                ref = prop_val.get("$ref", "") or prop_val.get("anyOf", [{}])[0].get("$ref", "")
                print(f"    ⭐ {prop_name}: $ref -> {ref.split('/')[-1]}")

# 3. 查 schedule 的具体 schema
print("\n\n=== Schedule schemas ===")
for name in sorted(defs.keys()):
    if "schedule" in name.lower():
        s = defs[name]
        props = list(s.get("properties", {}).keys())
        print(f"\n  {name}:")
        print(f"    type: {s.get('type', 'N/A')}")
        print(f"    props: {props}")
        if s.get("discriminator"):
            print(f"    discriminator: {s.get('discriminator')}")
