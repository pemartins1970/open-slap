import requests

# Debug do problema
login_data = {"email": "test@example.com", "password": "Test123@"}
r = requests.post('http://127.0.0.1:5150/auth/login', json=login_data)
print(f"Login: {r.status_code}")

if r.status_code == 200:
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    mcp_r = requests.get('http://127.0.0.1:5150/api/mcps', headers=headers)
    print(f"MCPs: {mcp_r.status_code}")
    print(f"Response headers: {dict(mcp_r.headers)}")
    print(f"Response content type: {mcp_r.headers.get('content-type')}")
    print(f"Response text (first 200 chars): {mcp_r.text[:200]}")
    
    if mcp_r.status_code == 200:
        try:
            data = mcp_r.json()
            mcps = data.get('mcps', [])
            print(f"Total: {len(mcps)}")
            for mcp in mcps:
                print(f"  - {mcp['id']} ({mcp['tier']}) - {mcp['name']}")
        except Exception as e:
            print(f"JSON decode error: {e}")
    else:
        print(f"Error: {mcp_r.text}")
else:
    print(f"Login error: {r.text}")
