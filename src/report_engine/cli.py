from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from report_engine.renderer import render_report
from report_engine.validator import PayloadValidationError, validate_payload


def _load_payload(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_validate(args: argparse.Namespace) -> int:
    payload = _load_payload(args.payload)
    _, warnings = validate_payload(payload, strict_images=args.strict_images)
    print("Payload validation passed.")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    payload = _load_payload(args.payload)
    warnings = render_report(
        args.template,
        args.output,
        payload,
        strict_images=args.strict_images,
    )
    print(f"Rendered: {args.output}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="report-engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--payload", required=True)
    validate_parser.add_argument("--strict-images", action="store_true")
    validate_parser.set_defaults(func=cmd_validate)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--template", required=True)
    render_parser.add_argument("--payload", required=True)
    render_parser.add_argument("--output", required=True)
    render_parser.add_argument("--strict-images", action="store_true")
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (PayloadValidationError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
