#!/usr/bin/env python3
import json, sys, os

repo = sys.argv[1]
path = sys.argv[2]

try:
    with open(path) as f:
        data = json.load(f)
    rust = data.get("Rust") or data.get("rust")
    if rust:
        print(f"{repo},{rust.get('files',0)},{rust.get('code',0)},{rust.get('comments',0)},{rust.get('blanks',0)}")
    else:
        print(f"{repo},0,0,0,0")
except Exception:
    print(f"{repo},0,0,0,0")
