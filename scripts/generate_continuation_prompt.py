#!/usr/bin/env python3
import json
from pathlib import Path


def fill_template(template_path, data):
    tmpl = Path(template_path).read_text()
    # Use Python's str.format for simple templating
    return tmpl.format(**data)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", required=True, help="Path to JSON data with fields for the template"
    )
    parser.add_argument(
        "--template",
        default="prompts/continuation_template.md",
        help="Path to the continuation template",
    )
    parser.add_argument("--out", help="Output path for rendered prompt")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text())
    result = fill_template(args.template, data)

    if args.out:
        Path(args.out).write_text(result)
    else:
        print(result)


if __name__ == "__main__":
    main()
