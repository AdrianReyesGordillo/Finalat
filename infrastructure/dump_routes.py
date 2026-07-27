import json
with open('/tmp/spec.json') as f:
    spec = json.load(f)
for path, methods in sorted(spec['paths'].items()):
    for method in methods:
        print(f"{method.upper():<8} {path}")
