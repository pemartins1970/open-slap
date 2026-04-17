import sys
import json
import re
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from datetime import datetime

RE_SHA256 = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)
RE_URI = re.compile(r"^https?://", re.IGNORECASE)

def _clean_text(s):
    if not isinstance(s, str):
        return ""
    v = s.strip()
    if v.startswith("`") and v.endswith("`") and len(v) >= 2:
        v = v[1:-1].strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        if len(v) >= 2:
            v = v[1:-1].strip()
    return v

def _iso8601(s):
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except Exception:
        return False

def canonicalize_url(url):
    url = _clean_text(url)
    if not url:
        return ""
    try:
        p = urlparse(url)
        scheme = (p.scheme or "").lower()
        netloc = (p.netloc or "").lower()
        path = p.path or ""
        query_pairs = []
        for k, v in parse_qsl(p.query, keep_blank_values=True):
            lk = k.lower()
            if lk.startswith("utm_") or lk in {"fbclid", "gclid", "sessionid"}:
                continue
            query_pairs.append((lk, v))
        query_pairs.sort(key=lambda kv: kv[0])
        query = urlencode(query_pairs, doseq=True)
        if path.endswith("/") and path.count("/") > 1 and not path.split("/")[-2].count("."):
            path = path[:-1]
        return urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return url

def compute_record_id(record_type, provider, url, version=None, title=None):
    cu = canonicalize_url(url or "")
    pv = str(provider or "").strip().lower()
    rt = str(record_type or "").strip().lower()
    vv = str(version or "").strip()
    tt = (title or "").strip().lower()
    base = "|".join([cu, pv, rt, vv or tt])
    h = hashlib.sha256()
    h.update(base.encode("utf-8"))
    return h.hexdigest()

def normalize_padxml(payload):
    if not isinstance(payload, dict):
        return payload
    src = payload.get("source")
    if isinstance(src, dict):
        if "provider" in src:
            src["provider"] = _clean_text(src.get("provider"))
        if "url" in src:
            src["url"] = _clean_text(src.get("url"))
    content = payload.get("content")
    if isinstance(content, dict):
        for k in ["download_url", "homepage_url"]:
            if k in content:
                content[k] = _clean_text(content.get(k))
        if "summary" in content and isinstance(content.get("summary"), str):
            content["summary"] = content["summary"].replace("\r", "").strip()
    rid = payload.get("record_id")
    if isinstance(rid, str) and RE_SHA256.match(rid.strip()):
        payload["record_id"] = rid.strip().lower()
    else:
        rt = payload.get("record_type")
        provider = (payload.get("source") or {}).get("provider")
        url = (payload.get("source") or {}).get("url")
        version = (payload.get("content") or {}).get("version")
        title = (payload.get("content") or {}).get("title")
        payload["record_id"] = compute_record_id(rt, provider, url, version=version, title=title)
    return payload

def _is_nonempty_str(x):
    return isinstance(x, str) and len(x.strip()) > 0

def _validate_required_keys(d, keys):
    missing = []
    for k in keys:
        if k not in d:
            missing.append(k)
    return missing

def _validate_source(src):
    errs = []
    if not isinstance(src, dict):
        return ["source must be object"]
    missing = _validate_required_keys(src, ["provider", "url", "collected_at", "robots", "crawl_policy", "checksums", "evidence"])
    if missing:
        errs.append("source missing: " + ",".join(missing))
        return errs
    if not _is_nonempty_str(_clean_text(src["provider"])):
        errs.append("source.provider invalid")
    url = _clean_text(src["url"])
    if not (_is_nonempty_str(url) and RE_URI.search(url)):
        errs.append("source.url invalid")
    if not (_is_nonempty_str(src["collected_at"]) and _iso8601(src["collected_at"])):
        errs.append("source.collected_at invalid")
    robots = src.get("robots", {})
    if not isinstance(robots, dict) or "allowed" not in robots or robots.get("allowed") is not True:
        errs.append("source.robots.allowed must be true")
    cp = src.get("crawl_policy", {})
    if not isinstance(cp, dict) or not _is_nonempty_str(cp.get("user_agent", "")):
        errs.append("source.crawl_policy.user_agent invalid")
    ch = src.get("checksums", {})
    if not isinstance(ch, dict) or not _is_nonempty_str(ch.get("content_sha256", "")) or not RE_SHA256.match(ch["content_sha256"]):
        errs.append("source.checksums.content_sha256 invalid")
    evid = src.get("evidence", [])
    if not isinstance(evid, list) or len(evid) < 1:
        errs.append("source.evidence minItems 1")
    return errs

def _text_sanitized(s):
    if not isinstance(s, str):
        return True
    if "<script" in s.lower():
        return False
    if "<" in s and ">" in s:
        return False
    return True

def _validate_content_software(content):
    errs = []
    if not isinstance(content, dict):
        return ["content must be object"]
    missing = _validate_required_keys(content, ["name", "os"])
    if missing:
        errs.append("content missing: " + ",".join(missing))
    name = content.get("name")
    if not _is_nonempty_str(name):
        errs.append("content.name invalid")
    osv = content.get("os")
    if osv not in ["windows", "linux", "macos", "android", "ios", "cross-platform"]:
        errs.append("content.os invalid")
    for k in ["download_url", "homepage_url"]:
        v = content.get(k)
        v2 = _clean_text(v) if isinstance(v, str) else v
        if v2 is not None and not (isinstance(v2, str) and (v2 == "" or RE_URI.search(v2))):
            errs.append(f"content.{k} invalid")
    for k in ["summary"]:
        v = content.get(k)
        if v is not None and not _text_sanitized(v):
            errs.append(f"content.{k} not sanitized")
    rd = content.get("release_date")
    if rd is not None and not (_is_nonempty_str(rd) and _iso8601(rd)):
        errs.append("content.release_date invalid")
    return errs

def validate_padxml_v1(payload):
    errs = []
    if not isinstance(payload, dict):
        return False, ["root must be object"]
    missing = _validate_required_keys(payload, ["schema_version", "record_type", "record_id", "source", "content"])
    if missing:
        return False, ["missing: " + ",".join(missing)]
    if payload.get("schema_version") != "padxml.v1":
        errs.append("schema_version must be padxml.v1")
    rt = payload.get("record_type")
    if rt not in ["software", "lead", "company", "article"]:
        errs.append("record_type invalid")
    rid = payload.get("record_id", "")
    if not (isinstance(rid, str) and RE_SHA256.match(rid.strip())):
        errs.append("record_id invalid")
    errs += _validate_source(payload.get("source"))
    if rt == "software":
        errs += _validate_content_software(payload.get("content"))
    sec = payload.get("security")
    if isinstance(sec, dict):
        if sec.get("sanitized") is not True:
            errs.append("security.sanitized must be true")
    ok = len(errs) == 0
    return ok, errs

def load_ndjson(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        dec = json.JSONDecoder()
        for line in f:
            s = line.strip()
            if not s:
                continue
            i = 0
            while i < len(s):
                while i < len(s) and s[i].isspace():
                    i += 1
                if i >= len(s):
                    break
                obj, end = dec.raw_decode(s, i)
                items.append(obj)
                i = end
    return items

def main():
    if len(sys.argv) < 2:
        print("usage: python padxml.py <file.ndjson|json>", file=sys.stderr)
        sys.exit(2)
    p = sys.argv[1]
    items = []
    if p.lower().endswith(".ndjson"):
        items = load_ndjson(p)
    else:
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
            if isinstance(obj, list):
                items = obj
            else:
                items = [obj]
    failures = 0
    for i, it in enumerate(items, 1):
        normalize_padxml(it)
        ok, errs = validate_padxml_v1(it)
        if not ok:
            failures += 1
            print(json.dumps({"index": i, "ok": False, "errors": errs}, ensure_ascii=False))
            continue
        print(json.dumps({"index": i, "ok": True, "record_id": it["record_id"]}, ensure_ascii=False))
    if failures:
        sys.exit(1)

if __name__ == "__main__":
    main()
