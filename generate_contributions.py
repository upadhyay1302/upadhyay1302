#!/usr/bin/env python3
"""
Fetches real GitHub contribution data via the GitHub GraphQL API
and generates panel-contributions.svg in the terminal-window style
used across this profile README.

Requires an environment variable GH_TOKEN with a token that has
access to read the target user's public contribution data.
"""
import os
import sys
import json
import urllib.request

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "upadhyay1302")
TOKEN = os.environ.get("GH_TOKEN")

if not TOKEN:
    print("ERROR: GH_TOKEN environment variable is not set.", file=sys.stderr)
    sys.exit(1)

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            weekday
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_contributions():
    body = json.dumps({"query": QUERY, "variables": {"login": GITHUB_USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": GITHUB_USERNAME,
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def level_for_count(count, max_count):
    if count == 0:
        return 0
    if max_count <= 1:
        return 4
    ratio = count / max_count
    if ratio < 0.25:
        return 1
    if ratio < 0.5:
        return 2
    if ratio < 0.75:
        return 3
    return 4


def build_svg(calendar):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    level_color = {0: "#161b22", 1: "#3b4048", 2: "#6e7681", 3: "#b1bac4", 4: "#f0f6fc"}
    max_day = max(
        (d["contributionCount"] for w in weeks for d in w["contributionDays"]),
        default=0,
    )

    active_days = sum(
        1 for w in weeks for d in w["contributionDays"] if d["contributionCount"] > 0
    )
    week_totals = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    best_week = max(week_totals) if week_totals else 0

    cell, gap = 9, 3
    start_x, start_y = 46, 250
    rects = []
    for wi, w in enumerate(weeks):
        x = start_x + wi * (cell + gap)
        for d in w["contributionDays"]:
            y = start_y + d["weekday"] * (cell + gap)
            lvl = level_for_count(d["contributionCount"], max_day)
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{level_color[lvl]}"><title>{d["date"]}: {d["contributionCount"]} '
                f'contributions</title></rect>'
            )

    n_weeks = len(weeks)
    grid_width = n_weeks * (cell + gap) - gap
    target_left, target_right = 32, 768
    raw_left, raw_right = start_x, start_x + grid_width
    sx = (target_right - target_left) / (raw_right - raw_left)
    tx = target_left - raw_left * sx
    heatmap_group = f'<g transform="translate({tx:.4f},0) scale({sx:.6f},1)">\n  ' + "\n  ".join(rects) + "\n</g>"

    max_wt = max(week_totals) if max(week_totals, default=0) > 0 else 1
    min_y, max_y = 140, 210
    chart_left, chart_right = 32, 768
    points = []
    for i, wt in enumerate(week_totals):
        x = chart_left + (chart_right - chart_left) * i / max(1, n_weeks - 1)
        y = max_y - (wt / max_wt) * (max_y - min_y)
        points.append((x, y))
    path_line = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    path_area = path_line + f" L {points[-1][0]:.1f} {max_y} L {points[0][0]:.1f} {max_y} Z"

    svg = f'''<svg width="800" height="400" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">
  <rect x="0.5" y="0.5" width="799" height="399" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <rect x="0" y="0" width="800" height="34" rx="10" fill="#161b22"/>
  <rect x="0" y="18" width="800" height="16" fill="#161b22"/>
  <circle cx="20" cy="17" r="6" fill="#ff5f56"/>
  <circle cx="40" cy="17" r="6" fill="#ffbd2e"/>
  <circle cx="60" cy="17" r="6" fill="#27c93f"/>
  <text x="400" y="22" text-anchor="middle" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="12" fill="#8b949e">{GITHUB_USERNAME}@github: ~/contributions</text>

  <text x="32" y="98" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="46" font-weight="700" fill="#f0f6fc">{total}</text>
  <text x="32" y="120" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="13" fill="#8b949e">contributions in the last year</text>
  <text x="768" y="70" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="22" font-weight="700" fill="#f0f6fc">{active_days}</text>
  <text x="768" y="86" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="12" fill="#8b949e">active days</text>
  <text x="768" y="112" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="22" font-weight="700" fill="#f0f6fc">{best_week}</text>
  <text x="768" y="128" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="12" fill="#8b949e">best week</text>

  <path d="{path_area}" fill="#f0f6fc" opacity="0.08"/>
  <path d="{path_line}" fill="none" stroke="#f0f6fc" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{points[-1][0]:.1f}" cy="{points[-1][1]:.1f}" r="3" fill="#f0f6fc"/>
  <line x1="32" y1="210" x2="768" y2="210" stroke="#30363d" stroke-width="1"/>

  <text x="36" y="270" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="10" fill="#8b949e">Mon</text>
  <text x="36" y="294" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="10" fill="#8b949e">Wed</text>
  <text x="36" y="318" text-anchor="end" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="10" fill="#8b949e">Fri</text>

  {heatmap_group}

  <text x="32" y="356" font-family="SFMono-Regular,Consolas,Menlo,Monaco,monospace" font-size="12" fill="#8b949e">Last updated automatically via GitHub Actions</text>
</svg>
'''
    return svg


def main():
    calendar = fetch_contributions()
    svg = build_svg(calendar)
    out_path = os.environ.get("OUTPUT_PATH", "panel-contributions.svg")
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"Wrote {out_path} — total contributions: {calendar['totalContributions']}")


if __name__ == "__main__":
    main()
