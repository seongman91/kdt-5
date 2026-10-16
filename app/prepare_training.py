"""Create a private environment file, roster and Orchestrate import files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import secrets

import yaml

from classroom_data import classroom_roster

BASE_DIR = Path(__file__).resolve().parent


def export_spec(source: Path, destination: Path, base_url: str, prefix: str, *, no_auth: bool = False) -> None:
    document = yaml.safe_load(source.read_text(encoding="utf-8"))
    document["servers"] = [{"url": base_url, "description": "Shared training API"}]
    if no_auth:
        document.pop("security", None)
        document.get("components", {}).pop("securitySchemes", None)
    else:
        document.setdefault("components", {}).setdefault("securitySchemes", {})["TrainingApiKey"] = {
            "type": "apiKey", "in": "header", "name": "X-API-Key",
        }
        document["security"] = [{"TrainingApiKey": []}]
    for path, path_item in document["paths"].items():
        for method, operation in path_item.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                if no_auth:
                    operation.pop("security", None)
                operation.setdefault("operationId", f"{prefix}_{method}_" + re.sub(r"\W+", "_", path).strip("_"))
    destination.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--students", type=int, default=20)
    parser.add_argument("--public-host", help="Public DNS or tunnel hostname, e.g. name.trycloudflare.com (without https://)")
    parser.add_argument("--tool-prefix", default="", help="Unique student label such as s01 for a shared Orchestrate instance")
    parser.add_argument("--output", type=Path, default=BASE_DIR / "generated")
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument("--no-auth", action="store_true", help="Allow calls without an API key (fictional training data only)")
    auth.add_argument("--api-key-auth", action="store_true", help="Enable API key authentication again")
    args = parser.parse_args()
    if args.tool_prefix and not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", args.tool_prefix):
        parser.error("--tool-prefix must start with a lowercase letter and use lowercase letters, digits or underscores")
    roster = classroom_roster(args.students)
    if not roster:
        parser.error("--students must be between 1 and 999")
    if args.public_host and (
        len(args.public_host) > 253
        or not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", args.public_host)
        or "." not in args.public_host
        or any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") for label in args.public_host.split("."))
    ):
        parser.error("--public-host must be a DNS hostname, without a protocol, path or port")

    env_path = BASE_DIR / ".env.training"
    settings = {}
    if env_path.exists():
        settings = dict(line.split("=", 1) for line in env_path.read_text(encoding="utf-8").splitlines() if "=" in line and not line.startswith("#"))
    mode = "none" if args.no_auth else "api_key" if args.api_key_auth else settings.get("TRAINING_AUTH_MODE", "api_key")
    if mode not in {"none", "api_key"}:
        parser.error("Invalid TRAINING_AUTH_MODE; use --no-auth or --api-key-auth")
    settings["TRAINING_AUTH_MODE"] = mode
    no_auth = mode == "none"
    if no_auth:
        settings["TRAINING_API_KEY"] = ""
    elif not settings.get("TRAINING_API_KEY"):
        settings["TRAINING_API_KEY"] = secrets.token_urlsafe(32)
    settings["TRAINING_STUDENTS"] = str(args.students)
    settings.setdefault("API_PORT", "8000")
    settings.setdefault("APP_DATA_DIR", "./training-data")
    if args.public_host:
        settings["PUBLIC_HOST"] = args.public_host.lower()
    else:
        settings.setdefault("PUBLIC_HOST", "localhost")
    env_path.write_text("\n".join(f"{key}={value}" for key, value in settings.items()) + "\n", encoding="utf-8")
    try:
        env_path.chmod(0o600)
    except PermissionError:
        # Windows bind mounts may allow writes but not POSIX mode changes.
        print("File permissions are managed by Windows for this folder; keep .env.training private.")

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "roster.json").write_text(json.dumps(roster, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["공용 실습 서버 배정표 (가상 데이터)", "초기값: 휴가 15일 / 출금계좌 5,000 EUR / 입금계좌 1,000 EUR / 한도 0 EUR", ""]
    for row in roster:
        lines.append(f"{row['student']} | 직원 {row['hr_name']} | 출금 {row['source_iban']} | 입금 {row['destination_iban']}")
    (args.output / "배정표.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    host = settings["PUBLIC_HOST"]
    base_url = f"https://{host}" if host != "localhost" else f"http://localhost:{settings['API_PORT']}"
    for prefix, source in (("hr", "hr_A.yaml"), ("bank", "bank_A.yaml")):
        operation_prefix = f"{prefix}_{args.tool_prefix}" if args.tool_prefix else prefix
        destination = args.output / f"{prefix}_training.yaml"
        export_spec(BASE_DIR / "openapi_templates" / source, destination, base_url, operation_prefix, no_auth=no_auth)
        if args.tool_prefix:
            document = yaml.safe_load(destination.read_text(encoding="utf-8"))
            document["info"]["title"] += f" {args.tool_prefix.upper()}"
            destination.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Prepared {len(roster)} students and {len(roster) * 2} fictional accounts.")
    if no_auth:
        print("Authentication: NONE. Anyone who knows the URL can read and change training data.")
    else:
        print(f"Private API key saved in {env_path.name}; it is not included in the import files.")
    print(f"OpenAPI server URL: {base_url}")
    if host == "localhost":
        print("Local validation only. Rerun with --public-host before importing into Orchestrate SaaS.")


if __name__ == "__main__":
    main()
