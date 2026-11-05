from pathlib import Path

p = Path("backend/app/api/v1/endpoints/artifacts.py")
txt = p.read_text(encoding="utf-8")

old_code = '''    # 2. If literal file exists in artifact directory, serve it directly
    if target_path.exists() and target_path.is_file():'''

new_code = '''    # 2. Check canonical aliases if exact target does not exist
    if not (target_path.exists() and target_path.is_file()):
        aliases = {
            "results.json": ["aggregate_comparison.json", "aggregate_results.json", "results.json"],
            "curves.csv": ["aggregate_comparison.csv", "aggregate_results.csv", "results.csv", "curves.csv"],
            "report.md": ["report.md"],
            "manifest.json": ["manifest.json"],
        }
        for cand in aliases.get(artifact_type.lower(), []):
            cand_p = (exp_dir / cand).resolve()
            if cand_p.exists() and cand_p.is_file():
                target_path = cand_p
                break

    # 3. If literal or aliased file exists in artifact directory, serve it directly
    if target_path.exists() and target_path.is_file():'''

assert old_code in txt, "Target not found"
txt = txt.replace(old_code, new_code, 1)
p.write_text(txt, encoding="utf-8")
print("Patched artifacts.py successfully")

