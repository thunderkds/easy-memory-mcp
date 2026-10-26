"""First-pass grading by required facts; every answer is also read by hand."""
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
FCM_SEND = r"sendNotificationToUser|sendNotificationToToken|sendKYCNotificationToUser"


ADMIN_PATH = r"admin\.service|updateRegularUserStatusById|updateVerifiedUserStatusById"


def grade(label, text):
    """1 = full answer, 0.5 = partial, 0 = wrong. Session A runs: None."""
    t = text or ""
    if label.startswith(("B_M", "S_M")):
        # Two real suspension paths: moderation decision and admin status update.
        mod = r"makeDecision|suspendByModeration" if label[0] == "B" \
            else r"decideModeration|suspendByModeration"
        if not re.search(FCM_SEND, t):
            return 0
        mod_ok = bool(re.search(mod, t)) and not (
            label[0] == "S" and stale_misled(t))
        paths = mod_ok + bool(re.search(ADMIN_PATH, t))
        return paths / 2
    if label.startswith("B_D"):
        no_logout = re.search(r"no (server[- ]side )?(logout|log-out|log out)"
                              r"|(not|n't|never)[^.\n]{0,60}(logout|log out|log-out)"
                              r"|(logout|log out)[^.\n]{0,60}(not|n't|no )",
                              t, re.I)
        unreg = re.search(r"unregister", t, re.I)
        return 1 if (no_logout and unreg) else 0.5 if unreg else 0
    if label.startswith("B_P"):
        # The three silent early returns, by name or by their line numbers.
        hits = sum(bool(re.search(p, t, re.I)) for p in [
            r"regularUserId|:22[5-9]",
            r"user (isn't |is not |not )?found|:23[4-7]|234-237",
            r"package (isn't |is not |not )?found|:24[3-6]|243-246"])
        if not re.search(r"handleCheckoutCompleted|pay-in\.service", t):
            return 0
        return 1 if hits >= 2 else 0.5
    return None


def stale_misled(text):
    """Cites makeDecision in moderation.service as the place to edit."""
    return bool(re.search(r"makeDecision", text or "")
                and not re.search(r"decideModeration", text or ""))


def tokens(d):
    u = d.get("usage") or {}
    return (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            + u.get("cache_read_input_tokens", 0)), u.get("output_tokens", 0)


# $/token, fitted exactly (error 0) from non-resumed runs. Needed because a
# resumed session's total_cost_usd also includes the original session's cost.
PRICE = (2e-6, 4e-6, 1e-7, 1e-5)


def run_cost(d):
    u = d.get("usage") or {}
    keys = ("input_tokens", "cache_creation_input_tokens",
            "cache_read_input_tokens", "output_tokens")
    return sum(u.get(k, 0) * p for k, p in zip(keys, PRICE))


def main():
    groups = defaultdict(list)
    for f in sorted(RESULTS.glob("*.json")):
        d = json.loads(f.read_text())
        label = d["_label"]
        key = label.rsplit("_", 1)[0] if label[0] in "BS" else label
        inp, out = tokens(d)
        ok = grade(label, d.get("result"))
        row = dict(label=label, inp=inp, out=out, tot=inp + out,
                   cost=run_cost(d), turns=d.get("num_turns"),
                   ok=ok, err=d.get("is_error"))
        if label.startswith("S_"):
            row["misled"] = stale_misled(d.get("result"))
        groups[key].append(row)
    print(f"{'group':22} {'n':>2} {'in(med)':>9} {'out(med)':>8} "
          f"{'cost(med)':>9} {'turns':>5} {'score':>7}")
    for key, rows in groups.items():
        med = lambda k: st.median(r[k] for r in rows)
        ok = sum(r["ok"] or 0 for r in rows)
        extra = ""
        if key.startswith("S_"):
            extra = f" misled={sum(r['misled'] for r in rows)}"
        print(f"{key:22} {len(rows):>2} {med('inp'):>9.0f} {med('out'):>8.0f} "
              f"{med('cost'):>9.4f} {med('turns'):>5.0f} "
              f"{ok:>4.1f}/{len(rows)}{extra}")
    (RESULTS.parent / "summary.json").write_text(
        json.dumps(groups, indent=1))


if __name__ == "__main__":
    main()
