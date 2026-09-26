from pathlib import Path

from dt_ai.core.io import digest, read_json, read_yaml

FILES = ("NPM_STANDARD.yaml", "VPM_STANDARD.yaml", "DELIVERY_VALIDATOR.yaml")


def rule_paths(value, path):
    if isinstance(value, dict):
        for key, child in value.items():
            if key not in {"source_page", "source_pages", "schema_source_pages"}:
                yield from rule_paths(child, path + "." + str(key))
    else:
        yield path


def load_profiles(root: Path):
    """Profiles are locked to the reviewed handoff; changes require a new review."""
    folder = root / "standards"
    lock = read_json((folder / "source/source-lock.json").read_bytes())
    source = folder / "source" / lock["pdf_file"]
    actual = digest(source.read_bytes())
    if actual != lock["pdf_sha256"]:
        raise ValueError("Source PDF hash mismatch")
    profiles = {}
    for name in FILES:
        path = folder / name
        data = read_yaml(path)
        if not isinstance(data, dict) or data.get("source", {}).get("sha256") != actual:
            raise ValueError(f"Invalid source reference in {name}")
        if digest(path.read_bytes()) != lock["profiles"][name]:
            raise ValueError(f"Unreviewed profile change: {name}; update traceability and decision first")
        profiles[name] = data
    trace = read_json((folder / "traceability.json").read_bytes())
    expected = {s["id"] for s in profiles["DELIVERY_VALIDATOR.yaml"]["stages"]}
    for kind in ("NPM", "VPM"):
        for group, value in profiles[f"{kind}_STANDARD.yaml"].items():
            if group not in {"standard", "version", "status", "source"}:
                expected.update(rule_paths(value, kind + "." + group))
    ids = [row["rule"] for row in trace]
    if set(ids) != expected or len(ids) != len(expected):
        raise ValueError("Traceability does not cover each original profile rule exactly once")
    for row in trace:
        if not row["pages"] or any(type(p) is not int or not 1 <= p <= 56 for p in row["pages"]):
            raise ValueError(f"Missing or invalid page evidence: {row['rule']}")
        if row["source_sha256"] != actual:
            raise ValueError(f"Stale traceability source: {row['rule']}")
    return profiles
