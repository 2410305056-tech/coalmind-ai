"""Copy local Supabase credentials and apply CoalMind migrations. Do not print secrets."""
from pathlib import Path
import json
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(r"C:\Users\YASHS\MonkeyCode\supabase-app\.env")
DEST = ROOT / ".env"
SQL_FILE = Path(__file__).with_name("migrations.sql")


def parse_env(path: Path) -> dict:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def write_env(src: dict) -> None:
    url = src.get("SUPABASE_URL", "")
    key = src.get("SUPABASE_SERVICE_ROLE_KEY") or src.get("SUPABASE_KEY", "")
    token = src.get("SUPABASE_ACCESS_TOKEN", "")
    ref = src.get("SUPABASE_PROJECT_REF", "")
    lines = [
        "STORE_TYPE=supabase",
        f"SUPABASE_URL={url}",
        f"SUPABASE_KEY={key}",
        f"SUPABASE_ACCESS_TOKEN={token}",
        f"SUPABASE_PROJECT_REF={ref}",
        "GROQ_API_KEY=",
        "GEMINI_API_KEY=",
    ]
    DEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def statements(sql: str):
    buf = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
    body = "\n".join(buf)
    for part in body.split(";"):
        stmt = part.strip()
        if stmt:
            yield stmt + ";"


def run_sql(token: str, ref: str, query: str) -> int:
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{ref}/database/query",
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", "replace")[:300]
        print("SQL_FAIL", exc.code, err)
        return exc.code


def main() -> None:
    if not SRC.exists():
        raise SystemExit("No source Supabase credentials found")
    src = parse_env(SRC)
    write_env(src)
    print("wrote .env STORE_TYPE=supabase")
    token = src.get("SUPABASE_ACCESS_TOKEN", "")
    ref = src.get("SUPABASE_PROJECT_REF", "")
    if not token or not ref:
        raise SystemExit("missing access token or project ref")
    ok = 0
    fail = 0
    for stmt in statements(SQL_FILE.read_text(encoding="utf-8")):
        code = run_sql(token, ref, stmt)
        if 200 <= code < 300:
            ok += 1
        else:
            fail += 1
    print("migration_ok", ok, "migration_fail", fail)


if __name__ == "__main__":
    main()
