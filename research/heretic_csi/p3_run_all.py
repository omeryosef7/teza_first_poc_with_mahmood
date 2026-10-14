"""Run the P3 descriptive chain (SVD -> write direction -> report) over all available factor files (S-082)."""
import os, subprocess, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
for s in ["p3_svd_analysis.py", "p3_write_direction.py", "p3_report.py"]:
    print("RUN", s, flush=True)
    subprocess.run([sys.executable, os.path.join(REPO, "research/heretic_csi", s)], check=True, cwd=REPO)
print("P3_ALL_DONE")
