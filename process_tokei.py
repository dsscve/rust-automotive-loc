import json
import os

output_file = "rust_loc_results.csv"
with open(output_file, "w") as out:
    out.write("repo,rust_files,rust_code,rust_comments,rust_blanks\n")
    work_dir = "work"
    for repo_dir in os.listdir(work_dir):
        path = os.path.join(work_dir, repo_dir, "tokei.json")
        if not os.path.exists(path):
            out.write(f"{repo_dir},0,0,0,0\n")
            continue
        with open(path) as f:
            data = json.load(f)
        rust = data.get("Rust") or data.get("rust")
        if rust:
            out.write(f"{repo_dir},{rust.get('files',0)},{rust.get('code',0)},{rust.get('comments',0)},{rust.get('blanks',0)}\n")
        else:
            out.write(f"{repo_dir},0,0,0,0\n")
