import csv
import os
import re

# --- Helper: count COSMIC-like movements ---
def count_movements(rs_file):
    e = x = r = w = 0
    try:
        with open(rs_file, 'r', encoding="utf-8", errors="ignore") as f:
            code = f.read()

            # --- Ignore async functions (0 CFP) ---
            code = re.sub(r'\basync fn\b.*?{.*?}', '', code, flags=re.DOTALL)

            # --- Entry / Exit ---
            e += len(re.findall(r'\bpub fn\b', code))          # public functions as Entry
            x += len(re.findall(r'-> .*String', code))        # functions returning data as Exit
            x += len(re.findall(r'println!', code))           # output as Exit

            # --- I/O movements ---
            r += len(re.findall(r'std::fs::read', code))      # read operations
            r += len(re.findall(r'std::fs::read_to_string', code))
            w += len(re.findall(r'std::fs::write', code))     # write operations
            w += len(re.findall(r'std::fs::write_all', code))

            # --- Structs: only count if used in function or impl block ---
            structs = re.findall(r'\bstruct\b\s+(\w+)', code)
            for struct_name in structs:
                # Count if referenced inside any function body
                pattern = r'fn\b.*?{[^}]*\b' + re.escape(struct_name) + r'\b'
                if re.search(pattern, code, flags=re.DOTALL):
                    e += 1

                # Count methods in impl blocks
                impl_pattern = r'impl\s+' + re.escape(struct_name) + r'\s*{([^}]*)}'
                for match in re.finditer(impl_pattern, code, flags=re.DOTALL):
                    methods = re.findall(r'\bfn\b', match.group(1))
                    e += len(methods)

    except:
        pass
    return e, x, r, w

# --- Input / Output CSVs ---
input_csv = "rust_loc_results.csv"
output_csv = "rust_loc_results_with_summary.csv"

total_eloc = 0
total_cfp = 0

with open(input_csv) as infile, open(output_csv, 'w', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ["Entry", "Exit", "Read", "Write", "CFP", "eLOC_per_CFP"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        repo = row["repo"]
        repo_dir = os.path.join("work", repo.replace("/", "_"))
        e_total = x_total = r_total = w_total = 0

        if os.path.exists(repo_dir):
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    if file.endswith(".rs"):
                        rs_file = os.path.join(root, file)
                        e, x, r, w = count_movements(rs_file)
                        e_total += e
                        x_total += x
                        r_total += r
                        w_total += w

        cfp = e_total + x_total + r_total + w_total
        eloc = int(row.get("rust_code", 0) or 0)
        ratio = round(eloc / cfp, 2) if cfp > 0 else 0

        total_eloc += eloc
        total_cfp += cfp

        row.update({
            "Entry": e_total,
            "Exit": x_total,
            "Read": r_total,
            "Write": w_total,
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
        "CFP": total_cfp,
        "eLOC_per_CFP": avg_ratio
    })
