"""Torch-free tests for scripts/gate3_trajectory_diag.py.

Uses synthetic in-tmp JSONL with known step scalars; asserts the computed
slopes/deltas match hand values and that a missing seed file does not crash.
No generation text is ever produced or read.
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "gate3_trajectory_diag.py")

spec = importlib.util.spec_from_file_location("gate3_diag", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _rec(objective, expected_rewards, sampled=None, proxy=None, seed=0, length=5):
    n = len(expected_rewards)
    sampled = sampled if sampled is not None else [0.0] * n
    proxy = proxy if proxy is not None else [0.0] * n
    steps = []
    for i in range(n):
        steps.append(
            {
                "step": i,
                "expected_reward": expected_rewards[i],
                "sampled_asr": sampled[i],
                "greedy_asr_proxy": proxy[i],
                "grad_norm": 1.0,
                "reward_variance": 0.5,
                "soft_prompt_norm": 4.0,
                "rewards": [0.0, 1.0],
            }
        )
    return {
        "objective": objective,
        "length": length,
        "seed": seed,
        "instruction": "label only snippet used here",
        "steps": steps,
    }


def test_linreg_slope_rising():
    # y = 0.1,0.2,0.3,0.4 over x=0..3 -> slope 0.1
    s = mod.linreg_slope([0, 1, 2, 3], [0.1, 0.2, 0.3, 0.4])
    assert abs(s - 0.1) < 1e-9


def test_linreg_slope_flat():
    s = mod.linreg_slope([0, 1, 2], [0.2, 0.2, 0.2])
    assert abs(s) < 1e-12


def test_linreg_slope_degenerate():
    assert mod.linreg_slope([1], [0.5]) is None
    assert mod.linreg_slope([2, 2, 2], [0.1, 0.2, 0.3]) is None


def test_analyze_run_rising():
    rec = _rec("reinforce", [0.1, 0.2, 0.3, 0.4])
    out = mod.analyze_run(rec)
    assert abs(out["exp_reward_slope"] - 0.1) < 1e-9
    assert abs(out["exp_reward_delta"] - 0.3) < 1e-9
    assert out["exp_reward_first"] == 0.1
    assert out["exp_reward_last"] == 0.4
    assert out["exp_reward_max"] == 0.4
    assert out["mean_grad_norm"] == 1.0
    assert out["mean_reward_variance"] == 0.5


def test_analyze_run_flat():
    rec = _rec("prefix_ce", [0.2, 0.2, 0.2])
    out = mod.analyze_run(rec)
    assert abs(out["exp_reward_slope"]) < 1e-12
    assert out["exp_reward_delta"] == 0.0


def test_greedy_proxy_transient_vs_final():
    # proxy hits 1.0 at step 1 (transient) but final step is 0.0
    rec = _rec("reinforce", [0.1, 0.2, 0.3], proxy=[0.0, 1.0, 0.0])
    out = mod.analyze_run(rec)
    assert out["greedy_proxy_ever_1"] == 1
    assert out["greedy_proxy_transient"] == 1
    assert out["greedy_proxy_final"] == 0
    assert out["greedy_proxy_first_step"] == 1

    # proxy hits 1.0 at final step -> final, not transient
    rec2 = _rec("reinforce", [0.1, 0.2, 0.3], proxy=[0.0, 0.0, 1.0])
    out2 = mod.analyze_run(rec2)
    assert out2["greedy_proxy_final"] == 1
    assert out2["greedy_proxy_transient"] == 0


def test_aggregate_positive_and_flat_counts():
    runs = [
        mod.analyze_run(_rec("reinforce", [0.1, 0.2, 0.3, 0.4])),  # +0.1
        mod.analyze_run(_rec("reinforce", [0.2, 0.2, 0.2])),       # flat
        mod.analyze_run(_rec("reinforce", [0.4, 0.3, 0.2, 0.1])),  # -0.1
    ]
    agg = mod.aggregate(runs)
    a = agg["reinforce"]
    assert a["n_runs"] == 3
    assert a["n_positive_slope"] == 1
    assert a["n_flat_slope"] == 1
    assert a["n_negative_slope"] == 1
    # mean slope = (0.1 + 0 - 0.1)/3 = 0
    assert abs(a["mean_exp_reward_slope"]) < 1e-9


def test_missing_seed_file_does_not_crash(tmp_path):
    conf = tmp_path / "conf"
    conf.mkdir()
    # only seed-0 reinforce present; all prefix_ce and seed1/seed2 absent
    with open(conf / "reinforce.jsonl", "w") as fh:
        fh.write(json.dumps(_rec("reinforce", [0.1, 0.2, 0.3])) + "\n")
    runs = mod.load_runs(str(conf))
    assert len(runs) == 1
    agg = mod.aggregate(runs)
    assert "reinforce" in agg
    # summary builder must not crash on a single-arm dir
    lines = mod.build_summary_lines(agg)
    assert any("reinforce" in ln for ln in lines)


def test_empty_dir_does_not_crash(tmp_path):
    runs = mod.load_runs(str(tmp_path))
    assert runs == []
    assert mod.aggregate(runs) == {}


def test_blank_lines_skipped(tmp_path):
    conf = tmp_path / "conf"
    conf.mkdir()
    with open(conf / "reinforce.jsonl", "w") as fh:
        fh.write("\n")
        fh.write(json.dumps(_rec("reinforce", [0.1, 0.2])) + "\n")
        fh.write("   \n")
    runs = mod.load_runs(str(conf))
    assert len(runs) == 1
