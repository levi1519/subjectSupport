import json, yaml, os, glob

paths = glob.glob(
    "C:/n8n/proyectos/subjectsSuport/AG/PHASE-1/**/requirements/*.json",
    recursive=True
) + [
    "C:/n8n/proyectos/subjectsSuport/AG/PHASE-2/requirements_integration.json",
    "C:/n8n/proyectos/subjectsSuport/AG/config/globalRequirements.json"
]

for path in paths:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    out = path.replace('.json', '.yaml')
    with open(out, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True,
                  default_flow_style=False, sort_keys=False)
    print(f"✅ {os.path.basename(out)}")

print(f"\nTotal: {len(paths)} archivos convertidos")
