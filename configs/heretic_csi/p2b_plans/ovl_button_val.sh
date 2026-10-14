set -euo pipefail
# AMENDMENT 5 rule on VALIDATION: button r4 VAL arms ran on n-501 (1036680), liveness/r1 on n-503 (1036679)
CW=button POP=val ORIG=1036679 OVLSFX=n501 bash outputs/heretic_csi/p2b/plans/ovl_template.sh
