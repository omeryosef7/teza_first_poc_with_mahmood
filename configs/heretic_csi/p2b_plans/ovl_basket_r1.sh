set -euo pipefail
# AMENDMENT 5 overlap job on n-501 (pinned): basket r1 resume host vs preempted 1023012 (n-503)
CW=basket ORIG=1023012 bash outputs/heretic_csi/p2b/plans/ovl_template.sh
# parent S-117: codeword-specific button n-501 vs n-503 coverage (button r4 arms ran on n-501; liveness on n-503 / 1023264)
CW=button ORIG=1023264 OVLSFX=n501 bash outputs/heretic_csi/p2b/plans/ovl_template.sh
