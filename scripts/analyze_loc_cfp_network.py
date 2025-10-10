#!/usr/bin/env python3
import csv
import os
import re

# --- Helper: count COSMIC-like movements including network I/O ---
def count_movements(rs_file):
    e = x = r = w = n = 0
    try:
        with open(rs_file, 'r', encoding="utf-8", errors="ignore") as f:
            code = f.read()
            # Exclude async functions
            async_fns = re.findall(r'async\s+fn\s+\w+', code)
            async_count = len(async_fns)

            # Entry: pub fn, struct methods
            entry_fns = re.findall(r'pub\s+fn\s+\w+', code)
            struct_methods = re.findall(r'impl\s+\w+\s*{[^}]*?fn\s+\w+', code, flags=re.DOTALL)
            e += len(entry_fns) + len(struct_methods)

            # Exit: functions returning String or println!
            x += len(re.findall(r'->\s*String', code))
            x += len(re.findall(r'println!', code))

            # Read: file read functions
            r += len(re.findall(r'std::fs::read', code))
            r += len(re.findall(r'read_to_string', code))

            # Write: file write functions
            w += len(re.findall(r'std::fs::write', code))
            w += len(re.findall(r'write_all', code))

            # Network I/O: reqwest, hyper, std::net
            n += len(re.findall(r'reqwest::', code))
            n += len(re.findall(r'hyper::', code))
            n += len(re.findall(r'std::net::', code))

            # Reduce async functions contribution to 0 CFP
            e -= async_count / 2
            x -= async_count / 2

            # Make sure counts are non-negative
            e = max(e, 0)
            x = max(x, 0)
    except Exception:
        pass
    return e, x, r, w, n

input_csv = "rust_loc_results.csv"
output_csv = "rust_loc_results_with_network.csv"

total_eloc = 0
total_cfp = 0

with open(input_csv) as infile, open(output_csv, 'w', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ["Entry", "Exit", "Read", "Write", "Network", "CFP", "eLOC_per_CFP"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        repo = row["repo"]
        repo_dir = os.path.join("work", repo.replace("/", "_"))
        e_total = x_total = r_total = w_total = n_total = 0

        if os.path.exists(repo_dir):
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    if file.endswith(".rs"):
                        rs_file = os.path.join(root, file)
                        e, x, r, w, n = count_movements(rs_file)
                        e_total += e
                        x_total += x
                        r_total += r
                        w_total += w
                        n_total += n

        cfp = e_total + x_total + r_total + w_total + n_total
        eloc = int(row.get("rust_code", 0) or 0)
        ratio = round(eloc / cfp, 2) if cfp > 0 else 0

        total_eloc += eloc
        total_cfp += cfp

        row.update({
            "Entry": e_total,
            "Exit": x_total,
            "Read": r_total,
            "Write": w_total,
            "Network": n_total,
            "CFP": cfp,
            "eLOC_per_CFP": ratio
        })
        writer.writerow(row)

    avg_ratio = round(total_eloc / total_cfp, 2) if total_cfp > 0 else 0
    writer.writerow({
        "repo": "TOTAL SUMMARY",
        "rust_files": "",
        "rust_code": total_eloc,
        "rust_comments": "",
        "rust_blanks": "",
        "Entry": "",
        "Exit": "",
        "Read": "",
        "Write": "",
        "Network": "",
        "CFP": total_cfp,
        "eLOC_per_CFP": avg_ratio
    })
