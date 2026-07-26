"""Project-local behavioral-objective package (Sprint Completion Plan §D3 + §D4).

Extends TROPT WITHOUT editing upstream `TROPT/tropt/*` (hard-rule compliant):

  * D3 (`proxy_ce_rerank`): proxy-CE behavioral reranking assembly — **NOT
    REINFORCE**. A §15.4/§15.6 hybrid wiring of TROPT `GCGPlusOptimizer`
    (differentiable Prefix-CE / MAC proposal + behavioral-reward selection).
  * D4 (`reinforce`): a pure-Python, model-agnostic REINFORCE estimator (RLOO
    advantages, signed teacher-forced CE weights, surrogate loss, GCGPlus
    adapter) — unit-testable on toy numbers with no torch.

The D4 estimator is pure Python (no torch) so it runs under
`/usr/bin/python3 -m pytest`; D3 imports TROPT/torch lazily inside its assembly
functions so the module and its pure pieces stay importable/testable there too.
"""

from . import candidate_pool  # noqa: F401  (pure-Python core; always importable)
from . import gpu_runner  # noqa: F401  (D4.5 runner; torch imports are lazy, so importing the module is torch-free)
from . import proxy_ce_rerank  # noqa: F401  (F4 fix: was in __all__ but unbound; torch/TROPT imports are lazy inside its functions, so importing the module is torch-free)
from . import reinforce  # noqa: F401  (pure-Python; always importable)
from . import reinforce_mac  # noqa: F401  (D4/D6 REINFORCE-MAC optimizer loop; torch imports are lazy, so importing the module is torch-free)
from . import rerank_runner  # noqa: F401  (pure-Python core; always importable)

__all__ = [
    "reinforce",
    "reinforce_mac",
    "proxy_ce_rerank",
    "candidate_pool",
    "rerank_runner",
    "gpu_runner",
]
