#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data source: Wikipedia NFL Draft pages (https://en.wikipedia.org/wiki/{year}_NFL_Draft)
This project scrapes publicly available draft pick tables from Wikipedia for educational purposes.
"""

# install requirements if not already present
# %pip install pandas plotly lxml html5lib beautifulsoup4 requests

import os
import argparse
import webbrowser
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.io as pio

# convert '#RRGGBB' to 'rgba(r,g,b,a)' for translucent links
def hex_to_rgba(hex_str, alpha=0.45):
    s = str(hex_str).strip().lstrip("#")
    if len(s) != 6:
        return f"rgba(102,102,102,{alpha})"
    r, g, b = int(s[0:2],16), int(s[2:4],16), int(s[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

# conferences
BIG_TEN = {
    "Penn State","Michigan","Ohio State","Michigan State","Iowa","Wisconsin","Minnesota","Nebraska",
    "Illinois","Indiana","Purdue","Rutgers","Northwestern","Maryland","USC","UCLA","Oregon","Washington"
}
SEC = {
    "Alabama","Georgia","LSU","Florida","Tennessee","Kentucky","Auburn","Ole Miss","Mississippi State",
    "Missouri","Texas A&M","Texas","Oklahoma","South Carolina","Vanderbilt","Arkansas"
}

# college colors
COLLEGE_COLORS = {
    "Penn State":"#041E42","Michigan":"#00274C","Ohio State":"#BB0000","Michigan State":"#18453B",
    "Iowa":"#FFCD00","Wisconsin":"#C5050C","Minnesota":"#7A0019","Nebraska":"#E41C38",
    "Illinois":"#13294B","Indiana":"#990000","Purdue":"#CEB888","Rutgers":"#CC0033",
    "Northwestern":"#4E2A84","Maryland":"#E03A3E","USC":"#990000","UCLA":"#2774AE",
    "Oregon":"#154733","Washington":"#4B2E83",
    "Alabama":"#9E1B32","Georgia":"#BA0C2F","LSU":"#461D7C","Florida":"#0021A5","Tennessee":"#FF8200",
    "Kentucky":"#0033A0","Auburn":"#0C2340","Ole Miss":"#CE1126","Mississippi State":"#660000",
    "Missouri":"#F1B82D","Texas A&M":"#500000","Texas":"#BF5700","Oklahoma":"#841617",
    "South Carolina":"#73000A","Vanderbilt":"#866D4B","Arkansas":"#9D2235",
}

# nfl team colors
NFL_COLORS = {
    "Arizona Cardinals":"#97233F","Atlanta Falcons":"#A71930","Baltimore Ravens":"#241773",
    "Buffalo Bills":"#00338D","Carolina Panthers":"#0085CA","Chicago Bears":"#0B162A",
    "Cincinnati Bengals":"#FB4F14","Cleveland Browns":"#311D00","Dallas Cowboys":"#041E42",
    "Denver Broncos":"#002244","Detroit Lions":"#0076B6","Green Bay Packers":"#203731",
    "Houston Texans":"#03202F","Indianapolis Colts":"#003A70","Jacksonville Jaguars":"#101820",
    "Kansas City Chiefs":"#E31837","Las Vegas Raiders":"#000000","Los Angeles Chargers":"#0080C6",
    "Los Angeles Rams":"#003594","Miami Dolphins":"#008E97","Minnesota Vikings":"#4F2683",
    "New England Patriots":"#002244","New Orleans Saints":"#D3BC8D","New York Giants":"#0B2265",
    "New York Jets":"#125740","Philadelphia Eagles":"#004C54","Pittsburgh Steelers":"#FFB612",
    "San Francisco 49ers":"#AA0000","Seattle Seahawks":"#002244","Tampa Bay Buccaneers":"#D50A0A",
    "Tennessee Titans":"#0C2340","Washington Commanders":"#5A1414",
}

# scrape one draft year into a tidy dataframe
def fetch_year(year: int) -> pd.DataFrame:
    url = f"https://en.wikipedia.org/wiki/{year}_NFL_Draft"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CFB-NFL-Sankey/1.0)"}
    html = requests.get(url, headers=headers).text
    tables = pd.read_html(html, flavor="bs4")

    draft_tables = [
        t for t in tables
        if any("Player" in str(c) for c in t.columns)
        and any(("College" in str(c)) or ("College/University" in str(c)) or ("School" in str(c)) for c in t.columns)
    ]
    if not draft_tables:
        raise RuntimeError(f"No draft tables found for {year} at {url}")

    draft_df = pd.concat(draft_tables, ignore_index=True)
    draft_df.columns = [str(c).strip().lower() for c in draft_df.columns]

    player_col = "player"
    college_col = next(c for c in ["college","college/university","school","university"] if c in draft_df.columns)
    team_col    = next(c for c in ["nfl team","team","club","to"] if c in draft_df.columns)
    pick_col = None
    for c in ["pick","overall","selection","overall pick","overall_pick"]:
        if c in draft_df.columns:
            pick_col = c
            break

    cols = [player_col, college_col, team_col] + ([pick_col] if pick_col else [])
    df = draft_df[cols].copy()
    df.columns = ["player","college","nfl_team"] + (["pick"] if pick_col else [])
    df["year"] = year

    df["player"]   = df["player"].astype(str).str.strip()
    df["college"]  = df["college"].astype(str).str.replace(r"\s*\[.*?\]", "", regex=True).str.strip()
    df["nfl_team"] = df["nfl_team"].astype(str).str.replace(r"\s*\(.*\)", "", regex=True).str.strip()
    if "pick" in df.columns:
        df["pick"] = pd.to_numeric(df["pick"], errors="coerce").astype("Int64")

    return df

# filter to chosen conferences
def filter_conferences(df: pd.DataFrame, conf_mode: str) -> pd.DataFrame:
    if conf_mode.lower() == "bigten":
        allow = BIG_TEN
    elif conf_mode.lower() == "sec":
        allow = SEC
    else:
        allow = BIG_TEN.union(SEC)
    return df[df["college"].isin(allow)].copy()

# build sankey with one link per player
def build_player_sankey(df: pd.DataFrame, year: int, title: str) -> go.Figure:
    data = df[df["year"] == year].copy()
    data = data.drop_duplicates(subset=["player","college","nfl_team"], keep="first")

    colleges = sorted(data["college"].unique())
    teams = sorted(data["nfl_team"].unique())
    nodes = colleges + teams
    node_index = {name:i for i,name in enumerate(nodes)}

    sources = data["college"].map(node_index).tolist()
    targets = data["nfl_team"].map(node_index).tolist()
    values  = [1]*len(data)

    node_colors = [COLLEGE_COLORS.get(n,"#666666") if n in colleges else NFL_COLORS.get(n,"#B0B0B0") for n in nodes]
    link_colors = [hex_to_rgba(COLLEGE_COLORS.get(c,"#666666"), alpha=0.45) for c in data["college"]]

    tooltips = []
    for _, r in data.iterrows():
        # keep pick optional; current README does not promise it
        pick_str = f" (Pick {int(r['pick'])})" if ("pick" in data.columns and pd.notna(r["pick"])) else ""
        tooltips.append(
            f"Player: {r['player']}{pick_str}<br>"
            f"College: {r['college']}<br>"
            f"Team: {r['nfl_team']}"
        )

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15, thickness=18, line=dict(color="black", width=0.3),
            label=nodes, color=node_colors
        ),
        link=dict(
            source=sources, target=targets, value=values,
            color=link_colors, customdata=tooltips,
            hovertemplate="%{customdata}<extra></extra>"
        )
    )])

    fig.update_layout(
        title=title,
        font=dict(size=12),
        hoverlabel=dict(align="left"),
        margin=dict(l=10,r=10,t=60,b=10)
    )
    return fig

# main cli
def main():
    parser = argparse.ArgumentParser(description="Build NCAA → NFL Sankey (one link per player).")
    parser.add_argument("--year", type=int, default=2025, help="Draft year, e.g. 2025")
    parser.add_argument("--confs", type=str, default="both", choices=["bigten","sec","both"], help="Conference filter")
    parser.add_argument("--out_html", type=str, default=None, help="Output HTML path (default: viz/cfb_sankey_{year}.html)")
    parser.add_argument("--out_csv", type=str, default=None, help="Output CSV path for tidy data (default: data/cfb_nfl_{year}.csv)")
    parser.add_argument("--open", action="store_true", help="Open the HTML in your default browser")
    args = parser.parse_args()

    year = args.year
    df = fetch_year(year)
    df = filter_conferences(df, args.confs)

    # set outputs
    out_html = args.out_html or os.path.join("viz", f"cfb_sankey_{year}.html")
    out_csv  = args.out_csv  or os.path.join("data", f"cfb_nfl_{year}.csv")
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    # save tidy data
    df[["player","college","nfl_team","year"]].to_csv(out_csv, index=False)

    # title
    title = f"From Saturdays to Sundays: Big Ten & SEC in the {year} NFL Draft<br><sup>Data: Wikipedia NFL Draft Pages</sup>"
    if args.confs.lower() == "bigten":
        title = f"From Saturdays to Sundays: Big Ten in the {year} NFL Draft<br><sup>Data: Wikipedia NFL Draft Pages</sup>"
    elif args.confs.lower() == "sec":
        title = f"From Saturdays to Sundays: SEC in the {year} NFL Draft<br><sup>Data: Wikipedia NFL Draft Pages</sup>"

    # build and write sankey
    fig = build_player_sankey(df, year, title)
    fig.write_html(out_html, include_plotlyjs="cdn", full_html=True)

    # optional open in browser
    if args.open:
        webbrowser.open("file://" + os.path.realpath(out_html))

# allow running as a notebook cell too
if __name__ == "__main__":
    # if running as a script: parse CLI
    try:
        main()
    except SystemExit:
        # if running in a notebook without args, fall back to defaults
        year = 2025
        df = fetch_year(year)
        df = filter_conferences(df, "both")
        pio.renderers.default = "browser"
        fig = build_player_sankey(df, year, f"From Saturdays to Sundays: Big Ten & SEC in the {year} NFL Draft<br><sup>Data: Wikipedia NFL Draft Pages</sup>")
        os.makedirs("viz", exist_ok=True)
        html_path = os.path.join("viz", f"cfb_sankey_{year}.html")
        fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)
        fig.show()
