"""Contextual-identity ("Bombness") probe package for the role-confusion sprint.

See docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md (§5, Appendix A) and
configs/manifests/role_probe_sprint_v1.json.

Modules:
  probe_dataset      -- corpus -> labeled extraction spec (pure Python, no torch)
  activation_extraction (later) -- spec -> residual activations at codeword positions
  contextual_identity_probe (later) -- activations -> fitted probe + metrics
"""
