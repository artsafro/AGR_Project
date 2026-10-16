"""Read-only FBX mesh inventory, also embedded in the standalone MAXScript.

No SDK or third-party modules. This reads the FBX container, never geometry.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import struct

_MAGIC = b"Kaydara FBX Binary  \x00\x1a\x00"
_MAX_DEPTH = 128
_MAX_NODES = 1_000_000
_MAX_SIZE = 2_147_483_648


def _clean_name(value):
    return value.split("\x00\x01", 1)[0].split("::", 1)[-1].strip()


def _mesh_names(data):
    """Return (version, names), rejecting malformed/ambiguous mesh inventories."""
    names = []
    if data.startswith(_MAGIC):
        if len(data) < 27:
            raise ValueError("Truncated binary FBX header")
        version = struct.unpack_from("<I", data, 23)[0]
        if not 6000 <= version <= 10000:
            raise ValueError("Unsupported FBX version")
        wide = version >= 7500
        header_size = 25 if wide else 13
        header_fmt = "<QQQB" if wide else "<IIIB"
        pos = 27
        nodes = 0

        def take(size, limit):
            nonlocal pos
            if size < 0 or pos + size > limit:
                raise ValueError("Truncated FBX property")
            result = data[pos:pos + size]
            pos += size
            return result

        def prop(limit):
            nonlocal pos
            code = take(1, limit)
            formats = {b"Y": "<h", b"C": "<?", b"I": "<i", b"F": "<f", b"D": "<d", b"L": "<q"}
            if code in formats:
                fmt = formats[code]
                return struct.unpack(fmt, take(struct.calcsize(fmt), limit))[0]
            if code in (b"S", b"R"):
                size = struct.unpack("<I", take(4, limit))[0]
                value = take(size, limit)
                return value.decode("utf-8", "strict") if code == b"S" else None
            sizes = {b"f": 4, b"d": 8, b"l": 8, b"i": 4, b"b": 1, b"c": 1}
            if code in sizes:
                count, encoding, packed = struct.unpack("<III", take(12, limit))
                if encoding not in (0, 1):
                    raise ValueError("Invalid FBX array encoding")
                size = count * sizes[code] if encoding == 0 else packed
                if encoding == 0 and packed != size:
                    raise ValueError("Invalid uncompressed FBX array length")
                take(size, limit)
                return None
            raise ValueError("Unknown FBX property type")

        def node(limit, depth):
            nonlocal pos, nodes
            if depth > _MAX_DEPTH:
                raise ValueError("FBX nesting limit exceeded")
            start = pos
            header = take(header_size, limit)
            end, count, plen, name_len = struct.unpack(header_fmt, header)
            if end == 0:
                if any(header):
                    raise ValueError("Invalid FBX terminator")
                return False
            nodes += 1
            if nodes > _MAX_NODES or count > _MAX_NODES:
                raise ValueError("FBX node/property limit exceeded")
            if end <= start or end > limit:
                raise ValueError("Invalid FBX node offset")
            name = take(name_len, end).decode("ascii", "strict")
            props_end = pos + plen
            if props_end > end:
                raise ValueError("Invalid FBX property list length")
            values = []
            for _ in range(count):
                value = prop(props_end)
                if name == "Model":
                    values.append(value)
            if pos != props_end:
                raise ValueError("FBX property count/length mismatch")
            if name == "Model":
                if len(values) >= 3 and isinstance(values[0], int) and isinstance(values[1], str):
                    raw, kind = values[1:3]
                elif len(values) == 2 and all(isinstance(v, str) for v in values):
                    raw, kind = values
                else:
                    raise ValueError("Invalid FBX Model properties")
                if kind == "Mesh":
                    names.append(_clean_name(raw))
            if pos < end:
                terminated = False
                while pos < end:
                    if not node(end, depth + 1):
                        terminated = True
                        break
                if not terminated or pos != end:
                    raise ValueError("Invalid FBX children terminator")
            return True

        while node(len(data), 0):
            pass
    else:
        text = data.decode("utf-8-sig", "strict")
        ver = re.search(r"\bFBXVersion\s*:\s*(\d+)", text)
        if not ver:
            raise ValueError("Missing ASCII FBX version")
        version = int(ver.group(1))
        if not 6000 <= version <= 10000:
            raise ValueError("Unsupported FBX version")
        # Lex quoted strings/comments first, so embedded braces cannot hide truncation.
        depth = 0
        quoted = False
        escaped = False
        comment = False
        declarations = list(re.finditer(r"^[ \t]*Model\s*:", text, re.M))
        declaration_positions = {text.index("Model", hit.start(), hit.end()) for hit in declarations}
        active_declarations = set()
        for offset, char in enumerate(text):
            if not quoted and not comment and offset in declaration_positions:
                active_declarations.add(offset)
            if comment:
                if char in "\r\n":
                    comment = False
            elif quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == ";":
                comment = True
            elif char == '"':
                quoted = True
            elif char == "{":
                depth += 1
                if depth > _MAX_DEPTH:
                    raise ValueError("FBX nesting limit exceeded")
            elif char == "}":
                depth -= 1
                if depth < 0:
                    raise ValueError("Unbalanced ASCII FBX braces")
        if quoted or depth:
            raise ValueError("Truncated ASCII FBX")
        # Only match actual node lines, not strings or semicolon comments.
        model = re.compile(r'^[ \t]*Model\s*:\s*(?:-?\d+\s*,\s*)?"((?:\\.|[^"\\])*)"\s*,\s*"([^"\r\n]+)"\s*\{', re.M)
        matches = [hit for hit in model.finditer(text) if text.index("Model", hit.start(), hit.end()) in active_declarations]
        if len(matches) != len(active_declarations):
            raise ValueError("Invalid ASCII FBX Model declaration")
        for hit in matches:
            if hit[2] == "Mesh":
                raw = hit[1].replace('\\"', '"').replace("\\\\", "\\")
                names.append(_clean_name(raw))
    seen = set()
    for name in names:
        if not name or "\x00" in name or any(ord(c) < 32 for c in name):
            raise ValueError("Empty or invalid FBX mesh name")
        if name.casefold() in seen:
            raise ValueError("Duplicate FBX mesh name: " + name)
        seen.add(name.casefold())
    if not names:
        raise ValueError("No Mesh models in FBX")
    return version, names


def _linked(path):
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _read_source(path):
    if path.stat().st_size > _MAX_SIZE:
        raise ValueError("FBX exceeds size limit: " + str(path))
    data = path.read_bytes()
    return data, hashlib.sha256(data).hexdigest()


def _npm_candidate(path, data, version, names):
    """NPM_STANDARD.yaml pp.10-13 naming + binary7400 gate, not full QA."""
    if not data.startswith(_MAGIC) or version != 7400:
        raise ValueError("NPM candidate requires binary FBX 7400/2014")
    match = re.fullmatch(r"[0-9]{4}_([A-Za-z0-9_]+)_(0[1-9]|1[0-9]|20|Ground)", path.stem)
    if len(path.stem) > 254 or not match:
        raise ValueError("NPM filename must be territory4_Address_01..20 or _Ground (max stem 254)")
    address, part = match.groups()
    if part == "Ground":
        valid = lambda name: name == "SM_" + address + "_Ground"
    else:
        pattern = re.compile(r"SM_" + re.escape(address) + r"_(00[1-9]|01[0-9]|020)_Main(?:Glass)?")
        valid = lambda name: pattern.fullmatch(name) is not None
    for name in names:
        if len(name) > 254 or not valid(name):
            raise ValueError("NPM mesh naming/address mismatch: " + name)


def analyze_folder(root, npm_only=False):
    root = Path(root).absolute()
    if not root.is_dir() or _linked(root):
        raise ValueError("Source root must be a real directory")
    root = root.resolve()
    files = []
    skipped = []
    keys = set()
    for folder, dirs, filenames in os.walk(root, followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        dirs[:] = sorted(d for d in dirs if not d.upper().startswith("NPM_FBX_") and not _linked(Path(folder) / d))
        for filename in sorted(filenames):
            path = Path(folder) / filename
            if path.suffix.lower() != ".fbx":
                continue
            relative = path.relative_to(root).as_posix()
            if _linked(path):
                skipped.append(dict(relative_path=relative, reason="Linked/reparse FBX source skipped"))
                continue
            if relative.casefold() in keys:
                raise ValueError("Duplicate FBX relative path: " + relative)
            keys.add(relative.casefold())
            try:
                data, digest = _read_source(path)
                version, names = _mesh_names(data)
                if npm_only:
                    _npm_candidate(path, data, version, names)
            except (ValueError, UnicodeError, struct.error, RecursionError) as error:
                if not npm_only:
                    raise
                skipped.append(dict(relative_path=relative, reason=str(error)))
                continue
            files.append(dict(relative_path=relative, path=str(path), sha256=digest, size=len(data), fbx_version=version, mesh_names=names))
    if not files:
        if npm_only:
            raise ValueError("No NPM candidates found; rejected FBX: " + str(len(skipped)))
        raise ValueError("No source FBX files found")
    payload = dict(schema_version=1, source_root=str(root), files=files, skipped=skipped)
    if npm_only:
        payload.update(selection_scope="npm_naming_binary7400_candidates_only", full_npm_verified=False)
    return payload


def validate_inventory(path, npm_only=False):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique_pairs)
    if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        raise ValueError("Unsupported inventory schema")
    root_value = payload.get("source_root")
    if not isinstance(root_value, str) or not Path(root_value).is_absolute():
        raise ValueError("Inventory source_root must be absolute")
    root = Path(root_value)
    if not root.is_dir() or _linked(root):
        raise ValueError("Inventory source_root is not a real directory")
    root = root.resolve()
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Empty inventory")
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Invalid inventory job")
        relative = item.get("relative_path")
        if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or "\x00" in relative:
            raise ValueError("Unsafe relative FBX path")
        parts = relative.split("/")
        if any(p in ("", ".", "..") or p.rstrip(" .") != p or p.upper().startswith("NPM_FBX_") for p in parts):
            raise ValueError("Unsafe relative FBX path")
        if PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).is_absolute() or Path(relative).suffix.lower() != ".fbx":
            raise ValueError("Unsafe relative FBX path")
        if relative.casefold() in seen:
            raise ValueError("Duplicate inventory path")
        seen.add(relative.casefold())
        source = root.joinpath(*parts)
        current = root
        for part in parts:
            current /= part
            if _linked(current):
                raise ValueError("Linked inventory source")
        if source.resolve().parent != root and root not in source.resolve().parents:
            raise ValueError("Inventory path escapes root")
        if not isinstance(item.get("path"), str) or Path(item["path"]).resolve() != source.resolve():
            raise ValueError("Inventory absolute path mismatch")
        data, digest = _read_source(source)
        if type(item.get("size")) is not int or item["size"] != len(data) or item.get("sha256") != digest:
            raise ValueError("FBX source changed: " + relative)
        version, names = _mesh_names(data)
        if npm_only:
            _npm_candidate(source, data, version, names)
        if item.get("mesh_names") != names or ("fbx_version" in item and item["fbx_version"] != version):
            raise ValueError("FBX mesh inventory mismatch: " + relative)
    return payload


def save_inventory(folder, output_dir=None, npm_only=False):
    payload = analyze_folder(folder, npm_only=npm_only)
    root = Path(payload["source_root"])
    destination = root
    if output_dir is not None:
        destination = Path(output_dir).absolute()
        if not destination.is_dir() or _linked(destination):
            raise ValueError("Inventory output must be a real directory")
        destination = destination.resolve()
        if destination == root:
            raise ValueError("Inventory output must differ from source root")
    elif npm_only:
        raise ValueError("NPM inventory requires a separate output workspace")
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = destination / ("npm_fbx_inventory_" + stamp + ".json")
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return str(target)


def verify_exports(inventory_path, output_root, npm_only=False):
    """Verify exported mesh membership only; this is not geometry/material QA."""
    payload = validate_inventory(inventory_path, npm_only=npm_only)
    output_root = Path(output_root).absolute()
    if not output_root.is_dir() or _linked(output_root):
        raise ValueError("Output root must be a real directory")
    output_root = output_root.resolve()
    if output_root == Path(payload["source_root"]).resolve():
        raise ValueError("Output root must differ from source root")
    reports = []
    for item in payload["files"]:
        output = output_root.joinpath(*item["relative_path"].split("/"))
        current = output_root
        for part in item["relative_path"].split("/"):
            current /= part
            if _linked(current):
                raise ValueError("Linked export output")
        if output.resolve() == Path(item["path"]).resolve():
            raise ValueError("Export output overlaps source")
        data, digest = _read_source(output)
        if not data:
            raise ValueError("Empty export: " + item["relative_path"])
        version, names = _mesh_names(data)
        if npm_only:
            _npm_candidate(output, data, version, names)
        expected = item["mesh_names"]
        if len(names) != len(expected) or {n.casefold() for n in names} != {n.casefold() for n in expected}:
            raise ValueError("Export mesh membership mismatch: " + item["relative_path"])
        reports.append(dict(relative_path=item["relative_path"], source_sha256=item["sha256"], output_sha256=digest,
                            size=len(data), fbx_version=version, mesh_names=names, verified=True,
                            verification_scope="mesh_membership_only", native_geometry_verified=False))
    report = dict(schema_version=1, inventory_path=str(Path(inventory_path).resolve()),
                  inventory_sha256=hashlib.sha256(Path(inventory_path).read_bytes()).hexdigest(),
                  output_root=str(output_root), files=reports, verified=True,
                  verification_scope="mesh_membership_only", native_geometry_verified=False)
    with (output_root / "export_report.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def _bridge(analyze):
    from pymxs import runtime as rt
    rt.AGR_NPMFbx_Error = ""
    rt.AGR_NPMFbx_Jobs = rt.Array()
    try:
        path = save_inventory(str(rt.AGR_NPMFbx_SourceRoot), output_dir=str(rt.AGR_NPMFbx_Workspace), npm_only=True) if analyze else str(rt.AGR_NPMFbx_JsonPath)
        payload = validate_inventory(path, npm_only=True)
        rt.AGR_NPMFbx_JsonPath = path
        rt.AGR_NPMFbx_SourceRoot = payload["source_root"]
        rt.AGR_NPMFbx_Jobs = rt.Array(*[rt.Array(item["relative_path"], rt.Array(*item["mesh_names"])) for item in payload["files"]])
    except Exception as error:
        rt.AGR_NPMFbx_Error = type(error).__name__ + ": " + str(error)


def agr_npm_fbx_analyze():
    _bridge(True)


def agr_npm_fbx_load():
    _bridge(False)


def agr_npm_fbx_verify_exports():
    from pymxs import runtime as rt
    rt.AGR_NPMFbx_Error = ""
    try:
        verify_exports(str(rt.AGR_NPMFbx_JsonPath), str(rt.AGR_NPMFbx_OutputRoot), npm_only=True)
    except Exception as error:
        rt.AGR_NPMFbx_Error = type(error).__name__ + ": " + str(error)
