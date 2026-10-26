"""Session memory store for experiment 02.

save(): keep a session's final answer plus a content hash of every repo file it
cites. pick(): rank stored memories against a new prompt with BM25 and flag the
ones whose cited files changed since they were saved. No model, no vectors.
"""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

STOP = set("""the and for are but not you all any can had her was one our out
has his how its may new now see two who did get let put say she too use what
when where which with this that from have will would there their them then
than into only also some such more most each other about after before does
doing done being been were your here just over very should could these those
code file files line lines repo answer question exactly existing edit
concisely references""".split())

REF = re.compile(
    r"([A-Za-z0-9_][A-Za-z0-9_.\-/]*\.(?:ts|tsx|js|jsx|java|py|kt|ftl|sql|xml|"
    r"yml|yaml|json|md))(?::\d+)?")
SKIP_DIRS = {"node_modules", ".git", "dist", "target", "build", "coverage"}


def tokens(text):
    out = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9_]*", text):
        parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", word).replace("_", " ")
        for p in {word.lower(), *parts.lower().split()}:
            if len(p) >= 3 and p not in STOP:
                out.append(p)
    return out


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_index(root):
    idx = {}
    for p in root.rglob("*"):
        if p.is_file() and not SKIP_DIRS & set(p.relative_to(root).parts):
            idx.setdefault(p.name, []).append(p.relative_to(root).as_posix())
    return idx


def cited_files(text, root):
    """Repo-relative paths cited in text; a bare name counts only if unique."""
    root = Path(root)
    idx, found = None, set()
    for ref in {m.group(1).lstrip("./") for m in REF.finditer(text)}:
        if (root / ref).is_file():
            found.add(ref)
            continue
        idx = idx or _file_index(root)
        cands = [c for c in idx.get(Path(ref).name, []) if c.endswith(ref)]
        if len(cands) == 1:
            found.add(cands[0])
    return sorted(found)


def save(store, seq, label, prompt, answer, root):
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    files = {f: _sha(Path(root) / f) for f in cited_files(answer, root)}
    rec = {"seq": seq, "label": label, "prompt": prompt, "answer": answer,
           "files": files}
    (store / f"{seq:03d}_{label}.json").write_text(json.dumps(rec, indent=1))
    return rec


def load(store):
    return [json.loads(p.read_text()) for p in sorted(Path(store).glob("*.json"))]


CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".java", ".py", ".kt", ".html",
            ".md", ".sql", ".xml", ".yml", ".yaml", ".ftl"}


def build_idf(root, out):
    """Document frequency of each token over the repo's own source files.

    Word weights come from the repo, not from the memory store, so a score
    does not depend on how many memories exist yet.
    """
    root, df, n = Path(root), Counter(), 0
    for p in root.rglob("*"):
        if (p.is_file() and p.suffix in CODE_EXT and p.stat().st_size < 300_000
                and not SKIP_DIRS & set(p.relative_to(root).parts)):
            df.update(set(tokens(p.read_text(errors="ignore"))))
            n += 1
    Path(out).write_text(json.dumps({"n": n, "df": df}))


def score(query, docs, idf_file, k1=1.2):
    """Weighted share of the query's words found in each doc, 0..1."""
    stats = json.loads(Path(idf_file).read_text())
    n, df = stats["n"], stats["df"]
    weight = {t: math.log((n + 1) / (df.get(t, 0) + 1)) + 1 for t in set(tokens(query))}
    best = sum(weight.values()) * (k1 + 1)
    out = []
    for d in docs:
        tf = Counter(tokens(d))
        s = sum(w * tf[t] * (k1 + 1) / (tf[t] + k1) for t, w in weight.items() if tf[t])
        out.append(s / best if best else 0.0)
    return out


def pick(store, prompt, root, idf_file, k=2, min_score=0.18, rel=0.5):
    """Top-k memories above an absolute floor and within rel of the best.

    Floor set on experiment 01's tapchat answers: same topic 0.23-0.49,
    false matches up to 0.17. Orderly is the unseen check.
    """
    recs = load(store)
    scores = score(prompt, [r["prompt"] + "\n" + r["answer"] for r in recs], idf_file)
    ranked = sorted(zip(scores, recs), key=lambda x: -x[0])
    if not ranked or ranked[0][0] < min_score:
        return [], ranked
    top = ranked[0][0]
    chosen = [(s, r) for s, r in ranked[:k] if s >= min_score and s >= rel * top]
    for _, r in chosen:
        r["changed"] = [f for f, h in r["files"].items()
                        if not (Path(root) / f).is_file()
                        or _sha(Path(root) / f) != h]
    return chosen, ranked
