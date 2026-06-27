from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from os_analyzer.analyzer import analyze_category
from os_analyzer.github_client import GitHubClient
from os_analyzer.report import build_category_report, build_summary_report, write_json, write_markdown

console = Console()


def load_categories(config_path: Path) -> list[dict]:
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("categories", [])


def print_summary(summary: dict) -> None:
    console.print("\n[bold cyan]Open Source Demand Analyzer[/bold cyan]\n")

    table = Table(title="Most Demanding Projects")
    table.add_column("Project", style="green")
    table.add_column("Category")
    table.add_column("Demand", justify="right")
    table.add_column("Tier")
    table.add_column("Stars", justify="right")

    for p in summary["top_demanding_projects"][:8]:
        table.add_row(
            p["full_name"],
            p["category"],
            f"{p['demand_score']:.1f}",
            p["tier"],
            f"{p['stars']:,}",
        )
    console.print(table)

    gap_table = Table(title="Projects With Most Feature Gaps")
    gap_table.add_column("Project", style="yellow")
    gap_table.add_column("Gaps", justify="right")
    gap_table.add_column("Top signals")

    for p in summary["projects_with_most_gaps"][:8]:
        gap_table.add_row(
            p["full_name"],
            str(p["gap_count"]),
            ", ".join(p["top_gaps"][:2]) or "—",
        )
    console.print(gap_table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze open source GitHub projects for demand and feature gaps."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/categories.yaml"),
        help="Path to categories YAML config",
    )
    parser.add_argument(
        "--per-category",
        type=int,
        default=5,
        help="Repositories to analyze per category (keep low without GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="Only analyze specific category IDs (repeatable)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory for JSON and Markdown reports",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    if not args.token:
        console.print(
            "[yellow]Tip:[/yellow] Set GITHUB_TOKEN for higher API rate limits (5000/hr vs 60/hr)."
        )

    client = GitHubClient(token=args.token)
    categories = load_categories(args.config)

    if args.categories:
        categories = [c for c in categories if c["id"] in args.categories]

    if not categories:
        raise SystemExit("No categories matched. Check --category IDs or config file.")

    category_reports = []
    for category in categories:
        console.print(f"Analyzing [bold]{category['name']}[/bold]...")
        repos = analyze_category(client, category, per_category=args.per_category)
        category_reports.append(build_category_report(category, repos))

    summary = build_summary_report(category_reports)
    write_json(summary, args.output_dir / "summary.json")
    write_json(
        {c["category_id"]: c for c in category_reports},
        args.output_dir / "by-category.json",
    )
    write_markdown(summary, args.output_dir / "REPORT.md")
    print_summary(summary)
    console.print(f"\n[green]Reports saved to[/green] {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()