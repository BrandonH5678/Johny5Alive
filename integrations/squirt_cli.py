#!/usr/bin/env python3
"""
Squirt Batch CLI - Process batch invoice/contract generation from CSV manifest
"""
import argparse, csv, pathlib, subprocess, sys

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
    return p.returncode == 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="CSV with job_type,input,style,out_name")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    outdir = pathlib.Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    with open(args.batch) as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            jt = row["job_type"]
            if jt == "invoice":
                cmd = f"python3 src/generate_invoice.py --input '{row['input']}' --style '{row.get('style','standard')}' --out '{outdir/row['out_name']}'"
            elif jt == "contract":
                cmd = f"python3 src/generate_contract.py --input '{row['input']}' --template '{row.get('style','sherertz')}' --out '{outdir/row['out_name']}'"
            else:
                print(f"Unknown job_type: {jt}", file=sys.stderr)
                continue
            run_cmd(cmd)

if __name__ == "__main__":
    main()
