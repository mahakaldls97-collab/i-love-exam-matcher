import sys, requests

key = sys.argv[1]
# List available models
for api in ['v1', 'v1beta']:
    r = requests.get(
        f'https://generativelanguage.googleapis.com/{api}/models',
        headers={'x-goog-api-key': key},
        timeout=10
    )
    print(f'--- {api} ({r.status_code}) ---')
    if r.status_code == 200:
        models = r.json().get('models', [])
        for m in models[:8]:
            print(' -', m.get('name', ''))
    else:
        print(r.text[:150])
