#!/usr/bin/env python3
"""Runs the whole package. Outputs land in output/."""
import subprocess, sys, os, time
HERE=os.path.dirname(os.path.abspath(__file__))
for script in ['01_asset_circuit.py','02_credit_prices_rents.py','03_verify_g1.py','04_pandemic_channel.py','05_check_against_paper.py']:
    print(f"\n{'='*70}\n  {script}\n{'='*70}")
    t0=time.time()
    r=subprocess.run([sys.executable, os.path.join(HERE,script)])
    if r.returncode:
        if script.startswith("05"):
            print("  [05 reported at least one mismatch - see output/05_check.txt]")
        else:
            sys.exit(f"FAILED: {script}")
    print(f"  [{time.time()-t0:.1f}s]")
print("\nAll scripts completed. See output/.")
