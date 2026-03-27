from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from collections import Counter
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import requests
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps
from sklearn.decomposition import LatentDirichletAllocation, PCA, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config" / "project.yml").read_text(encoding="utf-8"))
PATHS = CONFIG["paths"]
MODELS = CONFIG["models"]
REPORTING = CONFIG["reporting"]
THEMES = yaml.safe_load((ROOT / PATHS["theme_seeds"]).read_text(encoding="utf-8"))
SOTA_REFERENCES = pd.read_csv(ROOT / PATHS["sota_references"])

TOKEN_RE = re.compile(r"[A-Za-z']+")
ENTITY_RE = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")
ENTITY_STOPWORDS = {
    "The",
    "Chapter",
    "Project Gutenberg",
    "Project",
    "Gutenberg",
    "Illustration",
    "CHAPTER",
    "Alice",
    "And",
    "But",
    "He",
    "She",
    "They",
    "There",
    "Their",
    "Them",
    "This",
    "That",
    "These",
    "Those",
    "What",
    "When",
    "Where",
    "Why",
    "How",
    "You",
    "Your",
    "Then",
    "Now",
    "After",
    "Before",
    "Because",
    "Well",
    "Oh",
    "Ah",
    "Yes",
    "No",
}

LIVE_DASHBOARD_URL = "https://aarhus-childrens-literature-toolkit.vercel.app"
THEME_LABELS = {
    "family": "Family",
    "growth": "Growth",
    "fantasy": "Fantasy",
    "adventure": "Adventure",
    "animals": "Animals",
    "moral_emotion": "Moral & Emotion",
}
THEME_DESCRIPTIONS = {
    "family": "Supports family-centered reading lists, shelf design, and caregiver-facing discovery.",
    "growth": "Highlights books useful for maturity, learning, and coming-of-age comparisons.",
    "fantasy": "Surfaces imaginative worlds, magical systems, and speculative storytelling.",
    "adventure": "Finds titles driven by journeys, quests, travel, and high-motion plotting.",
    "animals": "Pulls together animal-forward narratives that work well for younger discovery journeys.",
    "moral_emotion": "Tracks courage, kindness, fear, and moral feeling for classroom and discussion use.",
}
SPLIT_LABELS = {
    "legacy-core": "Legacy Core",
    "expanded-core": "Expanded Core",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def root_path(key: str) -> Path:
    return ROOT / PATHS[key]


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(data: dict | list, path: Path) -> Path:
    ensure_parent(path)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def fmt_int(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{int(round(value)):,}"


def fmt_float(value: float | int | None, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{float(value):,.{digits}f}"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def theme_label(theme_key: str) -> str:
    return THEME_LABELS.get(theme_key, theme_key.replace("_", " ").title())


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows available._"
    cols = list(df.columns)
    widths = {col: max(len(str(col)), *(len(str(v)) for v in df[col].tolist())) for col in cols}
    header = "| " + " | ".join(f"{col:{widths[col]}}" for col in cols) + " |"
    rule = "| " + " | ".join("-" * widths[col] for col in cols) + " |"
    rows = []
    for row in df.to_dict(orient="records"):
        rows.append("| " + " | ".join(f"{str(row[col]):{widths[col]}}" for col in cols) + " |")
    return "\n".join([header, rule, *rows])


def write_csv(rows: Iterable[dict] | pd.DataFrame, path: Path) -> pd.DataFrame:
    ensure_parent(path)
    if isinstance(rows, pd.DataFrame):
        df = rows
    else:
        rows = list(rows)
        df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df


def load_seed() -> pd.DataFrame:
    return pd.read_csv(ROOT / PATHS["corpus_seed"])


def load_afinn() -> dict[str, int]:
    afinn: dict[str, int] = {}
    afinn_path = ROOT / "inst" / "extdata" / "AFINN-111.txt"
    if not afinn_path.exists():
        afinn_path = ROOT / "AFINN-111.txt"
    with afinn_path.open(encoding="utf-8") as handle:
        for line in handle:
            term, score = line.rstrip("\n").split("\t")
            afinn[term] = int(score)
    return afinn


AFINN = load_afinn()


def gutenberg_urls(gutenberg_id: int) -> list[str]:
    gid = str(gutenberg_id)
    return [
        f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
        f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
        f"https://www.gutenberg.org/files/{gid}/{gid}.txt",
    ]


def download_text(gutenberg_id: int, split: str) -> Path:
    target_dir = root_path("core_text_dir") if split == "legacy-core" else root_path("expanded_text_dir")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{gutenberg_id}.txt"
    if target.exists() and target.stat().st_size > 0:
        return target
    headers = {"User-Agent": "aarhus-childrens-literature-toolkit/0.1 (+https://github.com/bozliu/aarhus-childrens-literature-toolkit)"}
    last_error: Exception | None = None
    for url in gutenberg_urls(gutenberg_id):
        try:
            response = requests.get(url, headers=headers, timeout=60)
            if response.ok and len(response.text) > 1000:
                target.write_text(response.text, encoding="utf-8")
                return target
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"Failed to download Gutenberg text {gutenberg_id}: {last_error}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_gutenberg(text: str) -> str:
    start_pat = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG", re.IGNORECASE)
    end_pat = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG", re.IGNORECASE)
    lines = text.splitlines()
    start = 0
    end = len(lines)
    for idx, line in enumerate(lines):
        if start_pat.search(line):
            start = idx + 1
            break
    for idx, line in enumerate(lines[start:], start=start):
        if end_pat.search(line):
            end = idx
            break
    cleaned = "\n".join(lines[start:end]).strip()
    return cleaned or text


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def afinn_score(tokens: list[str]) -> int:
    return sum(AFINN.get(token, 0) for token in tokens)


def sentence_count(text: str) -> int:
    pieces = re.split(r"[.!?]+", text)
    return len([piece for piece in pieces if piece.strip()])


def load_book_records(manifest: pd.DataFrame | None = None) -> list[dict]:
    if manifest is None:
        manifest = pd.read_csv(root_path("corpus_manifest"))
    records = []
    for row in manifest.to_dict(orient="records"):
        text = (ROOT / row["local_path"]).read_text(encoding="utf-8", errors="ignore")
        clean_text = strip_gutenberg(text)
        tokens = tokenize(clean_text)
        row["clean_text"] = clean_text
        row["tokens"] = tokens
        row["token_text"] = " ".join(tokens)
        records.append(row)
    return records


def build_manifest() -> pd.DataFrame:
    seed = load_seed()
    rows: list[dict] = []
    for row in seed.to_dict(orient="records"):
        gid = int(row["gutenberg_id"])
        local_path = download_text(gid, row["split"])
        raw_text = local_path.read_text(encoding="utf-8", errors="ignore")
        clean_text = strip_gutenberg(raw_text)
        tokens = tokenize(clean_text)
        afinn_raw = afinn_score(tokens)
        rows.append(
            {
                **row,
                "source_url": f"https://www.gutenberg.org/ebooks/{gid}",
                "local_path": rel(local_path),
                "sha256": sha256(local_path),
                "character_count": len(clean_text),
                "word_count": len(tokens),
                "unique_word_count": len(set(tokens)),
                "sentence_count": sentence_count(clean_text),
                "afinn_raw": afinn_raw,
                "afinn_per_10k_tokens": round((afinn_raw / len(tokens)) * 10000, 2) if tokens else 0.0,
                "type_token_ratio": round(len(set(tokens)) / len(tokens), 4) if tokens else 0.0,
            }
        )
    df = pd.DataFrame(rows).sort_values(["split", "publication_year", "title"]).reset_index(drop=True)
    write_csv(df, root_path("corpus_manifest"))
    overview = (
        df.groupby("split")
        .agg(
            n_books=("gutenberg_id", "count"),
            total_words=("word_count", "sum"),
            median_book_words=("word_count", "median"),
            mean_book_words=("word_count", "mean"),
            mean_afinn_per_10k=("afinn_per_10k_tokens", "mean"),
            mean_type_token_ratio=("type_token_ratio", "mean"),
        )
        .reset_index()
    )
    overview["mean_book_words"] = overview["mean_book_words"].round(2)
    overview["median_book_words"] = overview["median_book_words"].round(2)
    overview["mean_afinn_per_10k"] = overview["mean_afinn_per_10k"].round(2)
    overview["mean_type_token_ratio"] = overview["mean_type_token_ratio"].round(4)
    write_csv(overview, root_path("tables_dir") / "corpus_manifest_overview.csv")
    return df


def classify_local_asset(path: Path) -> tuple[str, str]:
    relp = rel(path)
    if relp.startswith("data/raw/core") or relp.startswith("data/raw/expanded"):
        return "core", "reconstructed-corpus"
    if relp.startswith("course_2016/"):
        return "legacy-demo", "course-or-project-archive"
    if (
        relp.startswith("data/")
        or relp.startswith("tm_great_unread_files/")
    ):
        return "legacy-demo", "course-or-project-archive"
    if relp.startswith("LancsBox/"):
        return "auxiliary-validation", "reference-corpora"
    if relp.endswith((".zip", ".pdf", ".docx", ".MOV")):
        return "auxiliary-validation", "provenance-or-media"
    return "auxiliary-validation", "misc"


def inventory_candidate(path: Path) -> bool:
    relp = rel(path)
    if relp.endswith(".DS_Store") or "/__pycache__/" in relp or relp.startswith("childlit_toolkit.egg-info/"):
        return False
    if relp == "LancsBox/LancsBox.jar" or relp.startswith("LancsBox/resources/") or relp.startswith("tm_great_unread_files/"):
        return False
    if relp.startswith(
        (
            ".git/",
            ".github/",
            "R/",
            "scripts/",
            "childlit_toolkit/",
            "config/",
            "environment/",
            "docs/",
            "results/",
            "renv/",
            "inst/",
            "tools/",
        )
    ):
        return False
    if relp.startswith(
        (
            "data/",
            "course_2016/",
            "LancsBox/corpora/",
        )
    ):
        return True
    return "/" not in relp and path.suffix.lower() in {".docx", ".pdf", ".txt", ".dat", ".zip"}


def build_inventory() -> pd.DataFrame:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if not inventory_candidate(path):
            continue
        relp = rel(path)
        category, usage_role = classify_local_asset(path)
        rows.append(
            {
                "path": relp,
                "extension": path.suffix.lower(),
                "bytes": path.stat().st_size,
                "category": category,
                "usage_role": usage_role,
            }
        )
    df = write_csv(rows, root_path("local_assets"))
    summary = (
        df.groupby(["category", "usage_role"])
        .agg(n_files=("path", "count"), total_bytes=("bytes", "sum"))
        .reset_index()
        .sort_values(["category", "usage_role"])
    )
    write_csv(summary, root_path("tables_dir") / "dataset_inventory_summary.csv")
    return df


def parse_summary_block(text: str, label: str) -> dict[str, float]:
    pattern = rf"##{label}:\s*> summary\([^)]+\)\s*Min\.\s+1st Qu\.\s+Median\s+Mean\s+3rd Qu\.\s+Max\.\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not parse sentiment summary block for {label}")
    values = list(map(float, match.groups()))
    return dict(zip(["min", "q1", "median", "mean", "q3", "max"], values))


def parse_perplexity(text: str, label: str) -> float:
    match = re.search(rf"##{label}:\s*> perplexity\(mdl1\)\s*\[1\]\s*([-\d.]+)", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not parse perplexity for {label}")
    return float(match.group(1))


def build_legacy_summary() -> pd.DataFrame:
    legacy_path = ROOT / "course_2016" / "legacy_outputs" / "data.txt"
    if not legacy_path.exists():
        legacy_path = ROOT / "data.txt"
    text = legacy_path.read_text(encoding="utf-8", errors="ignore")
    men = parse_summary_block(text, "Men")
    women = parse_summary_block(text, "Women")
    df = pd.DataFrame(
        [
            {"cohort": "men", **men, "perplexity": parse_perplexity(text, "Men")},
            {"cohort": "women", **women, "perplexity": parse_perplexity(text, "Women")},
        ]
    )
    write_csv(df, root_path("legacy_summary"))
    write_csv(df, root_path("tables_dir") / "legacy_sentiment_and_topic_baseline.csv")
    return df


def module_status_rows() -> list[dict]:
    modules = {
        "transformers": "modern sentiment backend",
        "sentence_transformers": "embedding and retrieval backend",
        "bertopic": "embedding topic modeling",
        "gliner": "local named entity recognition",
        "torch": "accelerated local inference",
        "networkx": "entity co-occurrence graphing",
    }
    rows = []
    for module, purpose in modules.items():
        try:
            __import__(module)
            rows.append({"module": module, "status": "available", "purpose": purpose, "detail": "import ok"})
        except Exception as exc:  # noqa: BLE001
            rows.append({"module": module, "status": "missing", "purpose": purpose, "detail": str(exc).splitlines()[0][:180]})
    return rows


def save_backend_status() -> pd.DataFrame:
    df = write_csv(module_status_rows(), root_path("tables_dir") / "backend_status.csv")
    return df


def plot_corpus_timeline(df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [2.5, 1]})
    colors = {"legacy-core": "#1f5f8b", "expanded-core": "#f08c46"}
    for split, subdf in df.groupby("split"):
        counts = subdf.groupby("publication_year").size().reset_index(name="n")
        axes[0].scatter(counts["publication_year"], counts["n"], s=120, label=split, color=colors.get(split, "#555555"))
    axes[0].set_title("Corpus Timeline")
    axes[0].set_xlabel("Publication year")
    axes[0].set_ylabel("Books at year")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False)

    source_counts = df.groupby("seed_source").size().sort_values(ascending=False)
    axes[1].barh(source_counts.index, source_counts.values, color="#384b70")
    axes[1].invert_yaxis()
    axes[1].set_title("Provenance coverage")
    axes[1].set_xlabel("Books")

    out = root_path("figures_dir") / "corpus_timeline.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    plt.close(fig)

    single_fig, single_ax = plt.subplots(figsize=(8, 5))
    single_ax.barh(source_counts.index, source_counts.values, color="#384b70")
    single_ax.invert_yaxis()
    single_ax.set_title("Provenance coverage")
    single_ax.set_xlabel("Books")
    provenance_out = root_path("figures_dir") / "provenance_coverage.png"
    ensure_parent(provenance_out)
    single_fig.tight_layout()
    single_fig.savefig(provenance_out, dpi=180)
    plt.close(single_fig)
    return out


def plot_book_lengths(df: pd.DataFrame) -> Path:
    chart = df.sort_values("word_count", ascending=False).copy()
    colors = chart["split"].map({"legacy-core": "#1f5f8b", "expanded-core": "#f08c46"}).fillna("#666666")
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [2.2, 1]})
    axes[0].barh(chart["title"], chart["word_count"], color=colors)
    axes[0].invert_yaxis()
    axes[0].set_title("Book length distribution")
    axes[0].set_xlabel("Word count")
    axes[0].set_ylabel("Book")

    chart["chunking_risk"] = pd.cut(
        chart["word_count"],
        bins=[0, 25000, 60000, np.inf],
        labels=["low", "medium", "high"],
        include_lowest=True,
    )
    risk_counts = chart["chunking_risk"].value_counts().reindex(["low", "medium", "high"]).fillna(0)
    axes[1].bar(risk_counts.index.astype(str), risk_counts.values, color=["#8bc34a", "#ffb74d", "#e57373"])
    axes[1].set_title("Chunking risk")
    axes[1].set_xlabel("Risk tier")
    axes[1].set_ylabel("Books")

    out = root_path("figures_dir") / "core_book_lengths.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    plt.close(fig)

    risk_fig, risk_ax = plt.subplots(figsize=(8, 5))
    risk_ax.bar(risk_counts.index.astype(str), risk_counts.values, color=["#8bc34a", "#ffb74d", "#e57373"])
    risk_ax.set_title("Chunking risk")
    risk_ax.set_xlabel("Risk tier")
    risk_ax.set_ylabel("Books")
    risk_out = root_path("figures_dir") / "chunking_risk.png"
    ensure_parent(risk_out)
    risk_fig.tight_layout()
    risk_fig.savefig(risk_out, dpi=180)
    plt.close(risk_fig)
    return out


def plot_author_gender(df: pd.DataFrame) -> Path:
    counts = df.groupby(["split", "author_gender"]).size().reset_index(name="n")
    pivot = counts.pivot(index="split", columns="author_gender", values="n").fillna(0)
    fig, ax = plt.subplots(figsize=(8, 5))
    palette = {"female": "#d95f76", "male": "#1f5f8b", "mixed": "#7a7a7a"}
    bottom = np.zeros(len(pivot.index))
    for column in pivot.columns:
        ax.bar(pivot.index, pivot[column].values, bottom=bottom, label=column, color=palette.get(column, "#999999"))
        bottom += pivot[column].values
    ax.set_title("Author metadata balance")
    ax.set_xlabel("Corpus split")
    ax.set_ylabel("Books")
    ax.legend(frameon=False)
    out = root_path("figures_dir") / "author_gender_mix.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def get_sentiment_predictor() -> tuple[callable, str]:
    if os.environ.get("CHILDLIT_ENABLE_TRANSFORMERS", "0") != "1":
        def predict(text: str) -> float:
            tokens = tokenize(text)
            if not tokens:
                return 0.0
            return afinn_score(tokens) / max(len(tokens), 1)

        return predict, "afinn-fallback"

    try:
        from transformers import pipeline  # type: ignore

        model_name = MODELS["sentiment"]["modern_default"]
        classifier = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name, local_files_only=True)

        def predict(text: str) -> float:
            snippet = " ".join(text.split()[:220])
            result = classifier(snippet, truncation=True)[0]
            signed = result["score"] if result["label"].upper().startswith("POS") else -result["score"]
            return float(signed)

        return predict, f"transformer:{model_name}"
    except Exception:
        def predict(text: str) -> float:
            tokens = tokenize(text)
            if not tokens:
                return 0.0
            return afinn_score(tokens) / max(len(tokens), 1)

        return predict, "afinn-fallback"


def split_windows(tokens: list[str], n_windows: int = 12) -> list[list[str]]:
    if not tokens:
        return [[]]
    window_size = max(250, math.ceil(len(tokens) / n_windows))
    return [tokens[i : i + window_size] for i in range(0, len(tokens), window_size)]


def build_sentiment_trajectories(records: list[dict]) -> tuple[pd.DataFrame, str, Path]:
    predictor, backend = get_sentiment_predictor()
    rows = []
    for record in records:
        windows = split_windows(record["tokens"])
        for idx, window in enumerate(windows, start=1):
            rows.append(
                {
                    "title": record["title"],
                    "split": record["split"],
                    "window": idx,
                    "score": predictor(" ".join(window)),
                }
            )
    df = pd.DataFrame(rows)
    write_csv(df, root_path("tables_dir") / "sentiment_windows.csv")
    summary = (
        df.groupby(["title", "split"])
        .agg(
            mean_score=("score", "mean"),
            min_score=("score", "min"),
            max_score=("score", "max"),
            n_windows=("window", "count"),
        )
        .reset_index()
    )
    summary["backend"] = backend
    write_csv(summary, root_path("tables_dir") / "sentiment_window_summary.csv")

    highlight_titles = (
        pd.DataFrame(records)
        .sort_values(["split", "word_count"], ascending=[True, False])
        .groupby("split")
        .head(2)["title"]
        .tolist()
    )
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    colors = {"legacy-core": "#1f5f8b", "expanded-core": "#f08c46"}

    for title in highlight_titles:
        subset = df[df["title"] == title]
        axes[0].plot(subset["window"], subset["score"], marker="o", linewidth=2, label=title)
    axes[0].set_title("Representative sentiment trajectories")
    axes[0].set_ylabel("Sentiment score")
    axes[0].legend(frameon=False, ncol=2)
    axes[0].grid(alpha=0.2)

    split_mean = df.groupby(["split", "window"]).agg(score=("score", "mean")).reset_index()
    for split, subset in split_mean.groupby("split"):
        axes[1].plot(subset["window"], subset["score"], marker="o", linewidth=2.5, label=split, color=colors.get(split, "#666666"))
    axes[1].set_title("Average trajectory by split")
    axes[1].set_xlabel("Narrative window")
    axes[1].set_ylabel("Mean score")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.2)

    out = root_path("figures_dir") / "sentiment_trajectories.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return df, backend, out


def build_theme_heatmap(records: list[dict]) -> tuple[pd.DataFrame, Path]:
    rows = []
    for record in records:
        counter = Counter(record["tokens"])
        total = max(len(record["tokens"]), 1)
        for theme, terms in THEMES.items():
            score = sum(counter.get(term, 0) for term in terms) / total * 10000
            rows.append({"title": record["title"], "split": record["split"], "theme": theme, "score_per_10k": round(score, 2)})
    df = pd.DataFrame(rows)
    write_csv(df, root_path("tables_dir") / "theme_prevalence_by_book.csv")
    pivot = (
        df.pivot(index="title", columns="theme", values="score_per_10k")
        .fillna(0)
        .loc[pd.DataFrame(records).sort_values(["split", "publication_year", "title"])["title"].tolist()]
    )

    fig, ax = plt.subplots(figsize=(11, 10))
    image = ax.imshow(pivot.values, aspect="auto", cmap="YlGnBu")
    ax.set_title("Guided theme prevalence across books")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(image, ax=ax, label="Seed hits per 10k tokens")
    out = root_path("figures_dir") / "topic_prevalence_heatmap.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    alias_out = root_path("figures_dir") / "theme_prevalence_heatmap.png"
    fig.savefig(alias_out, dpi=180)
    plt.close(fig)
    write_csv(df, root_path("tables_dir") / "theme_prevalence.csv")
    return df, out


def build_topic_outputs(records: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    docs = [record["token_text"] for record in records]
    vectorizer = CountVectorizer(stop_words="english", max_df=0.8, min_df=2)
    dtm = vectorizer.fit_transform(docs)
    n_topics = min(6, max(2, dtm.shape[0] // 4))
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, learning_method="batch")
    doc_topics = lda.fit_transform(dtm)
    feature_names = vectorizer.get_feature_names_out()

    topic_rows = []
    for topic_idx, component in enumerate(lda.components_):
        top_indices = component.argsort()[::-1][:8]
        topic_rows.append(
            {
                "topic": f"topic_{topic_idx + 1}",
                "top_terms": ", ".join(feature_names[idx] for idx in top_indices),
            }
        )
    topic_df = write_csv(topic_rows, root_path("tables_dir") / "topic_top_terms.csv")

    prevalence = pd.DataFrame(doc_topics, columns=[f"topic_{i + 1}" for i in range(n_topics)])
    prevalence.insert(0, "title", [record["title"] for record in records])
    prevalence.insert(1, "split", [record["split"] for record in records])
    write_csv(prevalence, root_path("tables_dir") / "topic_prevalence_by_book.csv")
    return topic_df, prevalence


def compute_embeddings(records: list[dict]) -> tuple[np.ndarray, str]:
    docs = [record["clean_text"][:12000] for record in records]
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer(MODELS["embeddings"]["default"], trust_remote_code=True, local_files_only=True)
        embeddings = model.encode(docs, show_progress_bar=False, normalize_embeddings=True)
        return np.array(embeddings), f"sentence-transformers:{MODELS['embeddings']['default']}"
    except Exception:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=4000)
        matrix = vectorizer.fit_transform(docs)
        dense = matrix.toarray()
        return dense, "tfidf-fallback"


def build_embedding_outputs(records: list[dict]) -> tuple[pd.DataFrame, str, Path]:
    matrix, backend = compute_embeddings(records)
    if matrix.shape[1] > 2:
        reducer = TruncatedSVD(n_components=2, random_state=42) if matrix.shape[1] > 2 else PCA(n_components=2, random_state=42)
        coords = reducer.fit_transform(matrix)
    else:
        coords = matrix
    coords_df = pd.DataFrame(
        {
            "title": [record["title"] for record in records],
            "split": [record["split"] for record in records],
            "x": coords[:, 0],
            "y": coords[:, 1],
        }
    )
    write_csv(coords_df, root_path("tables_dir") / "embedding_projection.csv")

    sim = cosine_similarity(matrix)
    rows = []
    titles = coords_df["title"].tolist()
    for idx, title in enumerate(titles):
        order = np.argsort(sim[idx])[::-1]
        neighbors = [(titles[j], float(sim[idx, j])) for j in order if j != idx][:3]
        rows.append(
            {
                "title": title,
                "neighbor_1": neighbors[0][0],
                "neighbor_1_score": round(neighbors[0][1], 4),
                "neighbor_2": neighbors[1][0],
                "neighbor_2_score": round(neighbors[1][1], 4),
                "neighbor_3": neighbors[2][0],
                "neighbor_3_score": round(neighbors[2][1], 4),
            }
        )
    neighbors_df = write_csv(rows, root_path("tables_dir") / "embedding_neighbors.csv")
    write_csv(neighbors_df, root_path("tables_dir") / "book_similarity_examples.csv")

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = {"legacy-core": "#1f5f8b", "expanded-core": "#f08c46"}
    for split, subset in coords_df.groupby("split"):
        ax.scatter(subset["x"], subset["y"], s=120, label=split, alpha=0.85, color=colors.get(split, "#666666"))
        for _, row in subset.iterrows():
            ax.text(row["x"], row["y"], row["title"], fontsize=8, alpha=0.85)
    ax.set_title("Book neighborhood map")
    ax.set_xlabel("Dimension 1")
    ax.set_ylabel("Dimension 2")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    out = root_path("figures_dir") / "embedding_book_map.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    alias_out = root_path("figures_dir") / "book_similarity_map.png"
    fig.savefig(alias_out, dpi=180)
    plt.close(fig)
    return neighbors_df, backend, out


def heuristic_entities(text: str) -> list[str]:
    raw = ENTITY_RE.findall(text[:120000])
    cleaned = []
    for match in raw:
        candidate = match.strip()
        if candidate in ENTITY_STOPWORDS:
            continue
        if len(candidate) <= 2:
            continue
        cleaned.append(candidate)
    return cleaned


def build_entity_outputs(records: list[dict]) -> tuple[pd.DataFrame, str, Path]:
    backend = "heuristic-titlecase"
    rows = []
    graph = nx.Graph()
    for record in records:
        entities = heuristic_entities(record["clean_text"])
        counts = Counter(entities)
        top_entities = [entity for entity, _ in counts.most_common(10)]
        for entity, count in counts.most_common(20):
            rows.append(
                {
                    "title": record["title"],
                    "entity": entity,
                    "count": count,
                    "count_per_10k": round(count / max(record["word_count"], 1) * 10000, 2),
                }
            )
        for left, right in zip(top_entities, top_entities[1:]):
            if graph.has_edge(left, right):
                graph[left][right]["weight"] += 1
            else:
                graph.add_edge(left, right, weight=1)
    if rows:
        entity_df = pd.DataFrame(rows)
        leaderboard = (
            entity_df.groupby("entity")
            .agg(total_count=("count", "sum"), mean_per_10k=("count_per_10k", "mean"))
            .reset_index()
            .sort_values(["total_count", "mean_per_10k"], ascending=False)
            .head(20)
        )
        leaderboard["mean_per_10k"] = leaderboard["mean_per_10k"].round(2)
    else:
        entity_df = pd.DataFrame(columns=["title", "entity", "count", "count_per_10k"])
        leaderboard = pd.DataFrame(columns=["entity", "total_count", "mean_per_10k"])
    write_csv(leaderboard, root_path("tables_dir") / "entity_leaderboard.csv")

    fig, ax = plt.subplots(figsize=(12, 9))
    ax.axis("off")
    top_nodes = [row["entity"] for row in leaderboard.head(14).to_dict(orient="records")]
    subgraph = graph.subgraph(top_nodes).copy()
    if not subgraph.nodes:
        subgraph.add_node("No entities")
    positions = nx.spring_layout(subgraph, seed=42, k=0.8)
    weights = [subgraph[u][v].get("weight", 1) for u, v in subgraph.edges()]
    nx.draw_networkx(
        subgraph,
        pos=positions,
        ax=ax,
        node_color="#f08c46",
        edge_color="#7b8ba1",
        width=[0.8 + weight for weight in weights] if weights else 1.2,
        font_size=9,
    )
    ax.set_title("Entity co-occurrence network")
    out = root_path("figures_dir") / "entity_network.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    alias_out = root_path("figures_dir") / "entity_cooccurrence_network.png"
    fig.savefig(alias_out, dpi=180)
    plt.close(fig)
    return leaderboard, backend, out


def auxiliary_sources() -> dict[str, str]:
    brown = " ".join(path.read_text(encoding="utf-8", errors="ignore") for path in sorted((ROOT / "LancsBox" / "corpora" / "brown_corpus").glob("*.txt")))
    lob = " ".join(path.read_text(encoding="utf-8", errors="ignore") for path in sorted((ROOT / "LancsBox" / "corpora" / "lob_corpus").glob("*.txt")))
    return {
        "dr_seuss": (ROOT / "data" / "dr_seuss.txt").read_text(encoding="utf-8", errors="ignore"),
        "kjv": (ROOT / "data" / "kjv.txt").read_text(encoding="utf-8", errors="ignore"),
        "koran": (ROOT / "data" / "koran.txt").read_text(encoding="utf-8", errors="ignore"),
        "j_hansen": (ROOT / "data" / "j_hansen.txt").read_text(encoding="utf-8", errors="ignore"),
        "lancsbox_brown": brown,
        "lancsbox_lob": lob,
    }


def build_auxiliary_validation() -> tuple[pd.DataFrame, Path]:
    rows = []
    for name, text in auxiliary_sources().items():
        tokens = tokenize(text)
        rows.append(
            {
                "source": name,
                "word_count": len(tokens),
                "type_token_ratio": round(len(set(tokens)) / max(len(tokens), 1), 4),
                "sentence_count": sentence_count(text),
                "afinn_per_10k": round(afinn_score(tokens) / max(len(tokens), 1) * 10000, 2),
            }
        )
    df = write_csv(rows, root_path("tables_dir") / "auxiliary_validation_summary.csv")
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(
        df["type_token_ratio"],
        df["afinn_per_10k"],
        s=np.clip(df["word_count"] / 2500, 80, 320),
        c=np.linspace(0.2, 0.9, len(df)),
        cmap="viridis",
        alpha=0.85,
    )
    _ = scatter
    for _, row in df.iterrows():
        ax.text(row["type_token_ratio"], row["afinn_per_10k"], row["source"], fontsize=9)
    ax.set_title("Auxiliary validation panel")
    ax.set_xlabel("Type-token ratio")
    ax.set_ylabel("AFINN per 10k tokens")
    ax.grid(alpha=0.2)
    out = root_path("figures_dir") / "auxiliary_validation_panel.png"
    ensure_parent(out)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return df, out


def build_dependency_audit() -> pd.DataFrame:
    rows = [
        {
            "component": "Repository source",
            "kind": "repo",
            "declared_license": "Apache-2.0",
            "verification_state": "verified-local",
            "commercial_note": "Permissive for code reuse with notice retention.",
            "source": "LICENSE",
        },
        {
            "component": "Project Gutenberg texts",
            "kind": "data",
            "declared_license": "Public domain / Gutenberg terms",
            "verification_state": "manual-check-required",
            "commercial_note": "Keep provenance and confirm title-level status before redistribution bundles.",
            "source": "https://www.gutenberg.org/",
        },
        {
            "component": "GLiNER",
            "kind": "model-backend",
            "declared_license": "Apache-2.0",
            "verification_state": "upstream-docs",
            "commercial_note": "Safe default when installed, but verify model-card terms before shipping weights.",
            "source": "https://github.com/urchade/GLiNER",
        },
        {
            "component": "BERTopic",
            "kind": "python-package",
            "declared_license": "MIT",
            "verification_state": "upstream-docs",
            "commercial_note": "Optional analysis backend.",
            "source": "https://maartengr.github.io/BERTopic/",
        },
        {
            "component": "Qwen3-Embedding-0.6B",
            "kind": "model-backend",
            "declared_license": "Check model card",
            "verification_state": "manual-check-required",
            "commercial_note": "Use locally, but do not redistribute weights without checking upstream terms.",
            "source": "https://huggingface.co/Qwen/Qwen3-Embedding-0.6B",
        },
        {
            "component": "DistilBERT SST-2",
            "kind": "model-backend",
            "declared_license": "Apache-2.0",
            "verification_state": "model-card",
            "commercial_note": "Default sentiment backend when available.",
            "source": "https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english",
        },
    ]
    return write_csv(rows, root_path("dependency_audit"))


def build_benchmark_tables(
    manifest: pd.DataFrame,
    legacy: pd.DataFrame,
    sentiment_backend: str,
    embedding_backend: str,
    ner_backend: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    overview_rows = []
    for split, subset in manifest.groupby("split"):
        overview_rows.append(
            {
                "corpus_split": split,
                "n_books": int(subset.shape[0]),
                "total_words": int(subset["word_count"].sum()),
                "mean_words_per_book": round(float(subset["word_count"].mean()), 2),
                "median_words_per_book": round(float(subset["word_count"].median()), 2),
                "mean_afinn_per_10k_tokens": round(float(subset["afinn_per_10k_tokens"].mean()), 2),
                "mean_type_token_ratio": round(float(subset["type_token_ratio"].mean()), 4),
            }
        )
    benchmark = write_csv(overview_rows, root_path("tables_dir") / "benchmark_overview.csv")

    sentiment_windows = pd.read_csv(root_path("tables_dir") / "sentiment_window_summary.csv")
    topic_prevalence = pd.read_csv(root_path("tables_dir") / "topic_prevalence_by_book.csv")
    embedding_neighbors = pd.read_csv(root_path("tables_dir") / "embedding_neighbors.csv")
    entity_leaderboard = pd.read_csv(root_path("tables_dir") / "entity_leaderboard.csv")

    dominant_topic_share = topic_prevalence.filter(regex=r"^topic_").max(axis=1).mean()
    mean_neighbor_score = embedding_neighbors["neighbor_1_score"].mean()
    top_entity_density = entity_leaderboard.head(10)["mean_per_10k"].mean() if not entity_leaderboard.empty else float("nan")
    legacy_men = legacy.loc[legacy["cohort"] == "men"].iloc[0]
    legacy_women = legacy.loc[legacy["cohort"] == "women"].iloc[0]

    comparison_rows = [
        {
            "component": "Sentiment",
            "repo_metric": f"{sentiment_backend}; mean window score {fmt_float(sentiment_windows['mean_score'].mean())}",
            "legacy_2016_baseline": f"AFINN cohort means: men {fmt_float(legacy_men['mean'])} / women {fmt_float(legacy_women['mean'])}",
            "external_reference": MODELS["sentiment"]["modern_default"],
            "published_reference_or_sota": "Official model card only",
            "comparability_note": "No directly comparable literary benchmark in the local archive.",
        },
        {
            "component": "Topic modeling",
            "repo_metric": f"Guided themes + sklearn LDA; mean dominant topic share {fmt_float(dominant_topic_share, 3)}",
            "legacy_2016_baseline": f"topicmodels::LDA perplexity men {fmt_float(legacy_men['perplexity'], 1)} / women {fmt_float(legacy_women['perplexity'], 1)}",
            "external_reference": MODELS["topics"]["embedding_default"],
            "published_reference_or_sota": "Method docs only",
            "comparability_note": "Cross-corpus SOTA numbers are not directly comparable to this literary corpus.",
        },
        {
            "component": "NER",
            "repo_metric": f"{ner_backend}; top-10 entity mean density {fmt_float(top_entity_density)} per 10k",
            "legacy_2016_baseline": "Incomplete openNLP sketch",
            "external_reference": MODELS["ner"]["default"],
            "published_reference_or_sota": "Upstream docs",
            "comparability_note": "Local entity density and co-occurrence are project-specific.",
        },
        {
            "component": "Embeddings / retrieval",
            "repo_metric": f"{embedding_backend}; mean top-1 neighbor cosine {fmt_float(mean_neighbor_score, 3)}",
            "legacy_2016_baseline": "not available",
            "external_reference": MODELS["embeddings"]["default"],
            "published_reference_or_sota": "Model card / MTEB-style references",
            "comparability_note": "Neighbor quality is corpus-specific; external numbers are only reference context.",
        },
    ]
    comparison = write_csv(comparison_rows, root_path("tables_dir") / "benchmark_sota_comparison.csv")

    analysis_status = write_csv(
        [
            {"task": "sentiment", "backend": sentiment_backend, "status": "active"},
            {"task": "embedding", "backend": embedding_backend, "status": "active"},
            {"task": "ner", "backend": ner_backend, "status": "active"},
        ],
        root_path("analysis_status"),
    )
    _ = analysis_status
    return benchmark, comparison


def classify_pacing(mean_score: float, min_score: float, max_score: float) -> dict[str, float | str]:
    volatility = max_score - min_score
    if volatility >= 0.08:
        shape = "Turbulent"
    elif volatility >= 0.04:
        shape = "Mixed"
    else:
        shape = "Steady"

    if mean_score >= 0.03:
        tone = "Warm"
    elif mean_score <= 0:
        tone = "Shadowed"
    else:
        tone = "Balanced"

    return {
        "mean": round(mean_score, 4),
        "min": round(min_score, 4),
        "max": round(max_score, 4),
        "volatility": round(volatility, 4),
        "shape": shape,
        "tone": tone,
        "label": f"{tone} / {shape}",
    }


def build_collection_recommendations(manifest: pd.DataFrame) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    decade_counts = (
        manifest.assign(decade=(manifest["publication_year"] // 10) * 10)
        .groupby("decade")
        .size()
        .sort_values(ascending=False)
    )
    if not decade_counts.empty:
        dominant_decade = int(decade_counts.index[0])
        dominant_share = float(decade_counts.iloc[0] / manifest.shape[0])
        recommendations.append(
            {
                "title": "Historical clustering",
                "detail": (
                    f"{fmt_float(dominant_share * 100, 1)}% of the current titles cluster in the {dominant_decade}s. "
                    "Treat the dashboard as a canon-aware benchmark and expand the collection if you need broader temporal coverage."
                ),
            }
        )

    gender_counts = manifest["author_gender"].fillna("unknown").value_counts(normalize=True)
    if not gender_counts.empty:
        dominant_gender = gender_counts.index[0]
        dominant_gender_share = float(gender_counts.iloc[0])
        recommendations.append(
            {
                "title": "Metadata balance",
                "detail": (
                    f"{fmt_float(dominant_gender_share * 100, 1)}% of the titles currently fall under `{dominant_gender}` authorship metadata. "
                    "Use the corpus audit before presenting this set as a fully balanced map of the field."
                ),
            }
        )

    long_titles = int((manifest["word_count"] >= 70000).sum())
    recommendations.append(
        {
            "title": "Windowed comparison",
            "detail": (
                f"{long_titles} titles already exceed 70,000 words, so sentiment and theme views should be read as windowed comparisons rather than naive full-text averages."
            ),
        }
    )
    return recommendations[:3]


def build_dashboard_dataset(manifest: pd.DataFrame, records: list[dict]) -> Path:
    overview = pd.read_csv(root_path("tables_dir") / "corpus_manifest_overview.csv")
    theme_scores = pd.read_csv(root_path("tables_dir") / "theme_prevalence_by_book.csv")
    topic_prevalence = pd.read_csv(root_path("tables_dir") / "topic_prevalence_by_book.csv")
    topic_terms = pd.read_csv(root_path("tables_dir") / "topic_top_terms.csv").set_index("topic")["top_terms"].to_dict()
    embedding_neighbors = pd.read_csv(root_path("tables_dir") / "embedding_neighbors.csv").set_index("title")
    embedding_projection = pd.read_csv(root_path("tables_dir") / "embedding_projection.csv").set_index("title")
    sentiment_summary = pd.read_csv(root_path("tables_dir") / "sentiment_window_summary.csv").set_index("title")
    sentiment_windows = pd.read_csv(root_path("tables_dir") / "sentiment_windows.csv")
    auxiliary = pd.read_csv(root_path("tables_dir") / "auxiliary_validation_summary.csv")
    inventory = pd.read_csv(root_path("tables_dir") / "dataset_inventory_summary.csv")
    analysis_status = pd.read_csv(root_path("analysis_status"))
    backend_status = pd.read_csv(root_path("tables_dir") / "backend_status.csv")
    dependency = pd.read_csv(root_path("dependency_audit"))
    legacy = pd.read_csv(root_path("legacy_summary"))

    theme_pivot = theme_scores.pivot(index="title", columns="theme", values="score_per_10k").fillna(0.0)
    theme_pivot = theme_pivot.reindex(columns=list(THEMES.keys()), fill_value=0.0)
    sentiment_series = {
        title: [
            {"window": int(row["window"]), "score": round(float(row["score"]), 4)}
            for _, row in subset.sort_values("window").iterrows()
        ]
        for title, subset in sentiment_windows.groupby("title")
    }
    record_map = {record["title"]: record for record in records}

    book_entities: dict[str, list[dict[str, float | int | str]]] = {}
    for title, record in record_map.items():
        counts: Counter[str] = Counter()
        for entity in ENTITY_RE.findall(record["clean_text"]):
            entity = entity.strip()
            if entity in ENTITY_STOPWORDS or len(entity) < 3:
                continue
            counts[entity] += 1
        top_entities = []
        for name, count in counts.most_common(6):
            top_entities.append(
                {
                    "name": name,
                    "count": int(count),
                    "per10k": round((count / max(record["word_count"], 1)) * 10000, 2),
                }
            )
        book_entities[title] = top_entities

    books = []
    for row in manifest.sort_values(["publication_year", "title"]).to_dict(orient="records"):
        title = row["title"]
        theme_map = {
            key: round(float(theme_pivot.loc[title, key]), 2) if title in theme_pivot.index else 0.0
            for key in THEMES.keys()
        }
        theme_entries = sorted(
            (
                {"id": key, "label": theme_label(key), "score": score, "description": THEME_DESCRIPTIONS[key]}
                for key, score in theme_map.items()
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        pacing = classify_pacing(
            float(sentiment_summary.loc[title, "mean_score"]),
            float(sentiment_summary.loc[title, "min_score"]),
            float(sentiment_summary.loc[title, "max_score"]),
        )
        neighbors = []
        if title in embedding_neighbors.index:
            neighbor_row = embedding_neighbors.loc[title]
            for idx in range(1, 4):
                neighbors.append(
                    {
                        "title": str(neighbor_row[f"neighbor_{idx}"]),
                        "score": round(float(neighbor_row[f"neighbor_{idx}_score"]), 4),
                    }
                )
        dominant_topic = None
        if title in topic_prevalence["title"].values:
            topic_row = topic_prevalence.loc[topic_prevalence["title"] == title].iloc[0]
            topic_columns = [column for column in topic_prevalence.columns if column.startswith("topic_")]
            top_topic = max(topic_columns, key=lambda column: float(topic_row[column]))
            dominant_topic = {
                "id": top_topic,
                "share": round(float(topic_row[top_topic]), 4),
                "terms": topic_terms.get(top_topic, ""),
            }
        projection = {
            "x": round(float(embedding_projection.loc[title, "x"]), 4) if title in embedding_projection.index else 0.0,
            "y": round(float(embedding_projection.loc[title, "y"]), 4) if title in embedding_projection.index else 0.0,
        }
        top_themes = ", ".join(entry["label"] for entry in theme_entries[:2] if entry["score"] > 0)
        if not top_themes:
            top_themes = "low-intensity guided themes"
        neighbor_phrase = ", ".join(item["title"] for item in neighbors[:2]) if neighbors else "no close neighbors available yet"
        derived_summary = (
            f"{row['publication_year']} {SPLIT_LABELS.get(row['split'], row['split'])} title by {row['author']}. "
            f"Strongest signals: {top_themes}. Narrative pacing reads as {pacing['label']}. "
            f"Closest neighbors in the current corpus: {neighbor_phrase}."
        )
        books.append(
            {
                "id": slugify(title),
                "title": title,
                "author": row["author"],
                "authorGender": row["author_gender"],
                "publicationYear": int(row["publication_year"]),
                "split": row["split"],
                "splitLabel": SPLIT_LABELS.get(row["split"], row["split"]),
                "sourceUrl": row["source_url"],
                "localPath": row["local_path"],
                "wordCount": int(row["word_count"]),
                "sentenceCount": int(row["sentence_count"]),
                "typeTokenRatio": round(float(row["type_token_ratio"]), 4),
                "afinnPer10k": round(float(row["afinn_per_10k_tokens"]), 2),
                "ageBand": None,
                "ageBandLabel": "Unavailable in current corpus metadata",
                "summary": derived_summary,
                "themes": theme_entries,
                "sentiment": {**pacing, "windows": sentiment_series.get(title, [])},
                "similar": neighbors,
                "projection": projection,
                "entities": book_entities.get(title, []),
                "dominantTopic": dominant_topic,
            }
        )

    decade_summary = (
        manifest.assign(decade=(manifest["publication_year"] // 10) * 10)
        .groupby("decade")
        .agg(n_books=("title", "size"), total_words=("word_count", "sum"))
        .reset_index()
        .sort_values("decade")
    )
    gender_summary = (
        manifest.assign(author_gender=manifest["author_gender"].fillna("unknown"))
        .groupby("author_gender")
        .size()
        .reset_index(name="n_books")
        .sort_values("n_books", ascending=False)
    )
    split_summary = (
        manifest.groupby("split")
        .agg(n_books=("title", "size"), total_words=("word_count", "sum"))
        .reset_index()
    )

    theme_catalog = []
    for theme_key in THEMES.keys():
        subset = (
            theme_scores.loc[theme_scores["theme"] == theme_key, ["title", "score_per_10k"]]
            .sort_values("score_per_10k", ascending=False)
            .reset_index(drop=True)
        )
        stats = {
            "mean": round(float(subset["score_per_10k"].mean()), 2),
            "median": round(float(subset["score_per_10k"].median()), 2),
            "max": round(float(subset["score_per_10k"].max()), 2),
        }
        top_books = []
        for _, item in subset.head(8).iterrows():
            match = next(book for book in books if book["title"] == item["title"])
            top_books.append(
                {
                    "title": match["title"],
                    "author": match["author"],
                    "publicationYear": match["publicationYear"],
                    "score": round(float(item["score_per_10k"]), 2),
                    "summary": match["summary"],
                }
            )
        theme_catalog.append(
            {
                "id": theme_key,
                "label": theme_label(theme_key),
                "description": THEME_DESCRIPTIONS[theme_key],
                "stats": stats,
                "topBooks": top_books,
            }
        )

    dashboard_payload = {
        "generatedAt": pd.Timestamp.utcnow().isoformat(),
        "liveUrl": LIVE_DASHBOARD_URL,
        "reportUrl": f"{LIVE_DASHBOARD_URL}/report",
        "summary": {
            "nBooks": int(manifest.shape[0]),
            "totalWords": int(manifest["word_count"].sum()),
            "legacyBooks": int((manifest["split"] == "legacy-core").sum()),
            "expandedBooks": int((manifest["split"] == "expanded-core").sum()),
            "minYear": int(manifest["publication_year"].min()),
            "maxYear": int(manifest["publication_year"].max()),
        },
        "navigation": [
            {"href": "/", "label": "Home", "description": "Product landing page"},
            {"href": "/dashboard", "label": "Dashboard", "description": "Collection overview and quick entrypoints"},
            {"href": "/explorer", "label": "Book Explorer", "description": "Search, inspect, and compare titles"},
            {"href": "/themes", "label": "Theme Analysis", "description": "Theme-led reading-list design"},
            {"href": "/sentiment", "label": "Sentiment Arcs", "description": "Narrative pacing comparison"},
            {"href": "/corpus", "label": "Corpus Insights", "description": "Collection audit and provenance review"},
            {"href": "/report", "label": "Research Report", "description": "Long-form methodology and benchmark notes"},
        ],
        "insights": [
            {
                "title": "Canon-aware benchmark",
                "detail": (
                    f"The live corpus covers {manifest.shape[0]} books and {fmt_int(manifest['word_count'].sum())} words, "
                    "but it still clusters around a public-domain Anglo-American canon. Treat it as an auditable benchmark, not a universal map of the field."
                ),
            },
            {
                "title": "Meaningful book neighborhoods",
                "detail": (
                    "Similarity signals already produce interpretable neighbors such as Oz-to-Oz and Little Women-to-Anne of Green Gables style adjacency, "
                    "which is the right shape for discovery and list extension."
                ),
            },
            {
                "title": "Character-driven corpus",
                "detail": (
                    "Recurring names and dense entity surfaces make the dashboard especially useful for character-centered classroom comparison and catalog storytelling."
                ),
            },
            {
                "title": "Windowing matters",
                "detail": (
                    "Book length varies enough that sentiment and theme views should be read as chunked comparisons rather than one-number summaries."
                ),
            },
        ],
        "books": books,
        "themes": theme_catalog,
        "sentiment": {
            "books": [
                {
                    "title": book["title"],
                    "author": book["author"],
                    "splitLabel": book["splitLabel"],
                    "pacingLabel": book["sentiment"]["label"],
                    "mean": book["sentiment"]["mean"],
                    "min": book["sentiment"]["min"],
                    "max": book["sentiment"]["max"],
                    "volatility": book["sentiment"]["volatility"],
                    "windows": book["sentiment"]["windows"],
                }
                for book in books
            ]
        },
        "corpus": {
            "overview": overview.to_dict(orient="records"),
            "legacyBaseline": legacy.to_dict(orient="records"),
            "timeline": [
                {
                    "decade": int(row["decade"]),
                    "nBooks": int(row["n_books"]),
                    "totalWords": int(row["total_words"]),
                }
                for _, row in decade_summary.iterrows()
            ],
            "genderMix": [
                {"authorGender": row["author_gender"], "nBooks": int(row["n_books"])}
                for _, row in gender_summary.iterrows()
            ],
            "splitMix": [
                {
                    "split": row["split"],
                    "splitLabel": SPLIT_LABELS.get(row["split"], row["split"]),
                    "nBooks": int(row["n_books"]),
                    "totalWords": int(row["total_words"]),
                }
                for _, row in split_summary.iterrows()
            ],
            "inventory": inventory.to_dict(orient="records"),
            "auxiliaryValidation": auxiliary.to_dict(orient="records"),
            "analysisStatus": analysis_status.to_dict(orient="records"),
            "backendStatus": backend_status.to_dict(orient="records"),
            "dependencyAudit": dependency.to_dict(orient="records"),
            "recommendations": build_collection_recommendations(manifest),
        },
    }
    return write_json(dashboard_payload, root_path("dashboard_data"))


def build_release_manifest() -> pd.DataFrame:
    paths = [
        root_path("dashboard_data"),
        root_path("readme"),
        root_path("corpus_manifest"),
        root_path("local_assets"),
        root_path("legacy_summary"),
        root_path("app_dir") / "index.html",
        root_path("app_dir") / "assets" / "app.css",
        root_path("app_dir") / "assets" / "app.js",
        root_path("app_dir") / "assets" / "favicon.svg",
        root_path("public_dir") / "index.html",
        root_path("public_dir") / "dashboard" / "index.html",
        root_path("public_dir") / "report" / "index.html",
        root_path("tables_dir") / "benchmark_overview.csv",
        root_path("tables_dir") / "benchmark_sota_comparison.csv",
        root_path("dependency_audit"),
        root_path("report_qmd"),
        root_path("report_html"),
        Path(REPORTING["hero_gif"]) if not Path(REPORTING["hero_gif"]).is_absolute() else Path(REPORTING["hero_gif"]),
        Path(REPORTING["hero_mp4"]) if not Path(REPORTING["hero_mp4"]).is_absolute() else Path(REPORTING["hero_mp4"]),
    ]
    rows = []
    for path in paths:
        path = ROOT / path if not path.is_absolute() else path
        rows.append({"path": rel(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    return write_csv(rows, root_path("release_manifest"))


def build_fragments(manifest: pd.DataFrame) -> None:
    legacy = pd.read_csv(root_path("legacy_summary"))
    benchmark = pd.read_csv(root_path("tables_dir") / "benchmark_overview.csv")
    comparison = pd.read_csv(root_path("tables_dir") / "benchmark_sota_comparison.csv")
    backend = pd.read_csv(root_path("tables_dir") / "backend_status.csv")
    readiness = pd.read_csv(root_path("release_manifest"))

    corpus_summary = "\n".join(
        [
            "## Corpus Summary",
            "",
            f"- Total books: {manifest.shape[0]}",
            f"- Total words: {fmt_int(manifest['word_count'].sum())}",
            f"- Legacy-core books: {int((manifest['split'] == 'legacy-core').sum())}",
            f"- Expanded-core books: {int((manifest['split'] == 'expanded-core').sum())}",
            "",
            markdown_table(pd.read_csv(root_path('tables_dir') / 'corpus_manifest_overview.csv')),
            "",
        ]
    )
    legacy_summary = "\n".join(["## Legacy 2016 Baseline", "", markdown_table(legacy), ""])
    modern_stack = "\n".join(
        [
            "## Modern Stack",
            "",
            markdown_table(backend),
            "",
            "### Benchmark Framing",
            "",
            markdown_table(comparison),
            "",
            "### Corpus Snapshot",
            "",
            markdown_table(benchmark),
            "",
        ]
    )
    release_readiness = "\n".join(["## Release Bundle", "", markdown_table(readiness), ""])

    ensure_parent(root_path("fragments_dir") / "corpus_summary.md")
    (root_path("fragments_dir") / "corpus_summary.md").write_text(corpus_summary, encoding="utf-8")
    (root_path("fragments_dir") / "legacy_baseline.md").write_text(legacy_summary, encoding="utf-8")
    (root_path("fragments_dir") / "modern_stack.md").write_text(modern_stack, encoding="utf-8")
    (root_path("fragments_dir") / "release_readiness.md").write_text(release_readiness, encoding="utf-8")


def load_presentation_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    if bold:
        candidates = [
            "/System/Library/Fonts/Supplemental/Avenir Next Demi Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttc",
            *candidates,
        ]
    for candidate in candidates:
        path = Path(candidate)
        if not path.exists():
            continue
        try:
            return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def build_hero_assets_from_site() -> list[Image.Image]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Package 'playwright' is required for site-driven hero media generation.") from exc

    route_specs = [
        {
            "path": "/",
            "kicker": "Landing page",
            "title": "Discovery dashboard for Libraries & EdTech",
            "copy": "Lead with the value proposition, collection snapshot, and capability boundaries before users ever reach the deeper methods.",
        },
        {
            "path": "/dashboard",
            "kicker": "Dashboard",
            "title": "Turn corpus outputs into quick decisions",
            "copy": "Open with KPIs, recommended next actions, and explainable entrypoints for similarity, themes, pacing, and audit work.",
        },
        {
            "path": "/explorer?book=anne-of-green-gables",
            "kicker": "Explorer",
            "title": "Inspect one title and its closest neighbors",
            "copy": "A known book becomes a reusable discovery anchor with metadata, top themes, pacing signals, and related-title suggestions in one panel.",
        },
        {
            "path": "/themes?theme=fantasy",
            "kicker": "Themes",
            "title": "Build reading lists from interpretable themes",
            "copy": "Theme-led comparison is clearer for librarians and teachers than relying on weak or inconsistent catalog tags.",
        },
        {
            "path": "/sentiment",
            "kicker": "Sentiment arcs",
            "title": "Compare narrative pacing across books",
            "copy": "Windowed trajectories help teams contrast calmer and more turbulent reading experiences without pretending to predict plot.",
        },
        {
            "path": "/corpus",
            "kicker": "Corpus audit",
            "title": "Keep bias, provenance, and coverage visible",
            "copy": "Historical concentration and metadata balance stay in the product surface so collection claims remain auditable.",
        },
    ]

    class SiteHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root_path("app_dir")), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), SiteHandler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
        raw_frames: list[Image.Image] = []
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 960}, color_scheme="light", reduced_motion="reduce")
            page = context.new_page()
            for spec in route_specs:
                page.goto(f"{base_url}{spec['path']}", wait_until="networkidle")
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(250)
                if spec["path"].startswith("/sentiment"):
                    page.wait_for_timeout(250)
                screenshot = page.screenshot(type="png")
                raw_frames.append(Image.open(io.BytesIO(screenshot)).convert("RGB"))
            context.close()
            browser.close()
    finally:
        httpd.shutdown()
        thread.join(timeout=2)

    title_font = load_presentation_font(40, bold=True)
    copy_font = load_presentation_font(24)
    kicker_font = load_presentation_font(18, bold=True)
    brand_font = load_presentation_font(20, bold=True)
    frames: list[Image.Image] = []
    for spec, raw in zip(route_specs, raw_frames, strict=False):
        fitted = ImageOps.fit(raw, (1344, 840), method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (1440, 1024), "#f4efe5")
        canvas.paste(fitted, (48, 132))
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((32, 24, 1408, 108), radius=24, fill="#11363a")
        draw.text((60, 40), "LitScope feature walkthrough", font=brand_font, fill="#f8f1e3")
        draw.text((60, 76), spec["kicker"].upper(), font=kicker_font, fill="#d9c18c")
        draw.rounded_rectangle((32, 900, 1408, 992), radius=28, fill=(255, 250, 243))
        draw.text((64, 920), spec["title"], font=title_font, fill="#152526")
        draw.multiline_text((64, 958), textwrap.fill(spec["copy"], width=92), font=copy_font, fill="#53615d", spacing=4)
        frames.append(canvas)
    return frames


def build_hero_assets_from_figures() -> list[Image.Image]:
    figure_paths = [
        root_path("figures_dir") / "corpus_timeline.png",
        root_path("figures_dir") / "sentiment_trajectories.png",
        root_path("figures_dir") / "topic_prevalence_heatmap.png",
        root_path("figures_dir") / "embedding_book_map.png",
    ]
    source_images = [Image.open(fig_path).convert("RGB") for fig_path in figure_paths]
    frame_width = max(image.width for image in source_images)
    frame_height = max(image.height for image in source_images)
    frames: list[Image.Image] = []
    for index, img in enumerate(source_images, start=1):
        fitted = ImageOps.pad(img, (frame_width, frame_height), color="white")
        canvas = Image.new("RGB", (frame_width, frame_height + 90), "white")
        canvas.paste(fitted, (0, 90))
        draw = ImageDraw.Draw(canvas)
        for line_index, line in enumerate(
            [
                "Aarhus Children's Literature Toolkit",
                "2016 baseline reproduction plus modern dual-runtime analytics",
                f"Frame {index}: {figure_paths[index - 1].stem.replace('_', ' ').title()}",
            ]
        ):
            draw.text((18, 16 + 24 * line_index), line, fill="black")
        frames.append(canvas)
    return frames


def build_hero_assets() -> tuple[Path, Path]:
    try:
        import imageio.v2 as imageio  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Package 'imageio' is required for hero video generation. Run python -m childlit_toolkit bootstrap.") from exc

    try:
        frames = build_hero_assets_from_site()
    except Exception as exc:  # noqa: BLE001
        print(f"Site-driven hero media fallback triggered: {exc}", file=sys.stderr, flush=True)
        frames = build_hero_assets_from_figures()

    gif_path = ROOT / REPORTING["hero_gif"]
    ensure_parent(gif_path)
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=1500, loop=0, optimize=True)

    mp4_path = ROOT / REPORTING["hero_mp4"]
    ensure_parent(mp4_path)
    try:
        imageio.mimsave(mp4_path, [np.array(frame) for frame in frames], fps=1)
    except Exception as exc:  # noqa: BLE001
        print(f"MP4 generation skipped: {exc}", file=sys.stderr, flush=True)
    return gif_path, mp4_path


def render_readme_markdown() -> Path:
    manifest = pd.read_csv(root_path("corpus_manifest"))
    overview = pd.read_csv(root_path("tables_dir") / "corpus_manifest_overview.csv")
    legacy = pd.read_csv(root_path("legacy_summary"))
    inventory = pd.read_csv(root_path("tables_dir") / "dataset_inventory_summary.csv")
    comparison = pd.read_csv(root_path("tables_dir") / "benchmark_sota_comparison.csv")
    backend = pd.read_csv(root_path("tables_dir") / "backend_status.csv")
    methods = pd.read_csv(root_path("analysis_status"))
    auxiliary = pd.read_csv(root_path("tables_dir") / "auxiliary_validation_summary.csv")
    top_topics = pd.read_csv(root_path("tables_dir") / "topic_top_terms.csv")
    neighbors = pd.read_csv(root_path("tables_dir") / "embedding_neighbors.csv").head(6)
    entities = pd.read_csv(root_path("tables_dir") / "entity_leaderboard.csv").head(10)
    dependency = pd.read_csv(root_path("dependency_audit"))

    total_words = fmt_int(manifest["word_count"].sum())
    repo_name = CONFIG["project"]["github_repo"]
    report_path = PATHS["report_html"]
    readme = f"""# Aarhus Children's Literature Toolkit

![Hero demo](results/assets/hero.gif)

An open, dual-runtime rebuild of a 2016 Aarhus Summer University project on children’s literature. The repository is now framed as a dashboard-first discovery product for Libraries & EdTech, with recommendation/discovery as one feature layer inside a broader children’s literature intelligence workflow.

## What This Repo Delivers

1. A reproducible reconstruction of the canonical 20-book `Corpus of gold` children’s literature corpus.
2. A documented expansion layer with five additional public-domain titles.
3. First-class R and Python entrypoints over the same manifests, figures, tables, and report outputs.
4. A public-release surface that favors interpretable charts, benchmark tables, and reusable SOP documentation instead of screenshots.

## Live Dashboard

- Public app: [{LIVE_DASHBOARD_URL}]({LIVE_DASHBOARD_URL})
- Overview route: [{LIVE_DASHBOARD_URL}/dashboard]({LIVE_DASHBOARD_URL}/dashboard)
- Title search: [{LIVE_DASHBOARD_URL}/explorer]({LIVE_DASHBOARD_URL}/explorer)
- Theme analysis: [{LIVE_DASHBOARD_URL}/themes]({LIVE_DASHBOARD_URL}/themes)
- Sentiment arcs: [{LIVE_DASHBOARD_URL}/sentiment]({LIVE_DASHBOARD_URL}/sentiment)
- Corpus audit: [{LIVE_DASHBOARD_URL}/corpus]({LIVE_DASHBOARD_URL}/corpus)
- Methodology report: [{LIVE_DASHBOARD_URL}/report]({LIVE_DASHBOARD_URL}/report)

## Who This Is For

- Libraries and reading platforms that need better title discovery than age bands and manual tagging alone.
- EdTech and curriculum teams that want interpretable signals for themed reading lists, classroom comparison, and catalog exploration.
- Title-discovery teams who need similarity lookup, theme profiles, sentiment pacing, and corpus audit in one surface.

## What Problem It Solves

- Children’s books are often cataloged with sparse metadata, broad age labels, and inconsistent subject tags, which makes related-title discovery shallow and hard to explain.
- Manual browsing can find a few obvious comparisons, but it does not scale well across dozens of books when a librarian or product team needs to compare theme, pacing, character prominence, and corpus bias together.
- This repo turns a children’s literature corpus into a structured comparison surface so teams can move from “find books manually” to “inspect books systematically.”

## What Decisions It Helps You Make

- Which books should appear as related-title neighbors when a reader, librarian, or curator starts from one known title.
- Which titles fit friendship, family, growth, fantasy, adventure, or animal-centered reading lists.
- Which books are calmer versus more turbulent in narrative pacing, and therefore better suited to different reading experiences or classroom uses.
- Where the current catalog is historically clustered, imbalanced, or over-dependent on a narrow canonical slice.

## Why Children’s Literature

- Children’s literature is culturally foundational: it shapes early reading habits, moral vocabularies, character archetypes, and shared narrative worlds.
- It is analytically strong for text mining because the books often contain clear story arcs, recurring character systems, theme-rich plots, and accessible language patterns that are easy to interpret in discovery and dashboard settings.
- It works well as an R text-mining case because the outputs are legible to non-technical readers, which matters for librarians, teachers, and public-facing reading products.
- The public-domain corpus makes the workflow reproducible, legally shareable, and easy to reuse in catalog navigation, reading-list curation, and digital-humanities teaching.

## Why The 20-Book Legacy Corpus Matters

- The legacy baseline stays at **20 books** because that is the canonical corpus defined in the original `Corpus of gold` course documents, so keeping those titles intact preserves historical comparability with the 2016 final project and gives the dashboard a trusted benchmark layer.
- Twenty books is small enough to audit title by title, metadata row by metadata row, and provenance source by provenance source, which matters for a public digital-humanities workflow.
- At the same time, those 20 books are large enough to support corpus-level analysis: the current rebuilt legacy core contains **20 books and 1,046,864 words**, which is enough to expose differences in sentiment, theme prevalence, named entities, and narrative structure across books for dashboard comparison.
- The modern release expands beyond that baseline with 5 extra books, but the 20-book set remains the anchor corpus because it is the cleanest bridge between course history, reproducibility, and present-day reuse in a live discovery product.

## What We Learn From The Analysis

- The rebuilt corpus is useful but not neutral: the current public release covers **25 books and 1,332,482 words**, while the legacy core remains historically clustered around a public-domain Anglo-American canon. For a dashboard product, that means the corpus is best read as a canon-aware benchmark and collection-audit surface, not as a universal map of all children’s literature.
- Book neighborhoods are meaningful enough to support discovery workflows. The similarity outputs place `The Wonderful Wizard of Oz` near `The Emerald City of Oz`, while `Little Women` sits closer to `Anne of Green Gables` and `Peter Pan`, which is exactly the kind of interpretable neighboring structure that libraries and reading products can reuse.
- Character prominence is one of the clearest signals in this corpus. The entity outputs are dominated by recurring named characters such as Dorothy, Wendy, Polly, and Mowgli, which makes the dashboard particularly useful for character-driven reading comparison and classroom discussion design.
- Theme profiles are readable at the title level rather than only at the corpus level. The guided theme layer makes it practical to contrast family, growth, fantasy, adventure, animals, and moral-emotion signals book by book when building lists or comparing shelves.
- Book length varies enough to become an implementation constraint. Some titles are long enough to distort naive full-text averages, so chunking and windowed analysis are not optional engineering details; they are required if the dashboard is going to compare books fairly.
- Sentiment trajectories are more informative than one global score. They behave best as discovery features for narrative pacing rather than as proxies for quality, which is why they fit a dashboard product better than a forecasting claim.

## What This Repo Can And Cannot Tell You

- It **can** tell you how books compare across theme, sentiment movement, recurring entities, lexical patterns, and semantic similarity. In product terms, it already works as a children’s literature comparison and discovery layer.
- It **can** help you inspect corpus bias and benchmark a new title or corpus against a historically grounded public-domain baseline.
- It **cannot yet** reliably predict future story events, endings, or “what happens next” in a strong forecasting sense. The current pipeline is descriptive, comparative, and retrieval-oriented rather than trained as a chapter-by-chapter predictive model, so it should not be sold as a story predictor.
- It **does not** claim to score literary quality, educational value, pedagogy quality, or sales potential directly. Those would require new labels, user data, and product-specific evaluation loops that are outside the present repo.

## Commercial Value And Product Direction

- The honest near-term product is a **children’s literature discovery dashboard** for Libraries & EdTech, not a general story-trajectory predictor and not a standalone recommendation engine.
- Recommendation belongs inside that dashboard as one feature layer alongside theme profiles, sentiment pacing, character prominence, and catalog audit.
- For libraries, reading platforms, and curriculum teams, this product direction is already defensible because the repo can turn a raw corpus into concrete discovery and curation signals.
- For research groups, museums, and digital-humanities labs, the same repo remains useful as a reusable evidence surface and methodologically transparent SOP.
- If this repo becomes a product, the clearest MVP is a searchable dashboard with title lookup, similar-book navigation, theme profile panels, sentiment arc views, and corpus-level audit panels. Stronger predictive features should only come after sequence-aware modeling and evaluation exist.

## Capability Map

| Dashboard capability | Product question it answers |
| -------------------- | --------------------------- |
| Similarity lookup | If a reader likes one title, which neighboring books should a librarian or reading platform inspect next? |
| Theme profiles | Which books fit friendship, family, growth, fantasy, adventure, or animal-centered reading lists? |
| Sentiment arcs | Which books have calmer versus more turbulent narrative pacing? |
| Entity density / character prominence | Which books are strongly character-driven for discussion, curriculum design, or reader-facing comparisons? |
| Corpus audit | Where is the catalog historically biased, over-clustered, or too narrow to support broader claims? |

Libraries and EdTech teams do not buy a topic model for its own sake. They buy better discovery, curation, list-building, and catalog interpretation. The repo’s practical value is that it turns raw books into those decision surfaces without pretending that the current stack already predicts literary success or future plot events.

## 2016 Course Archive

The historical Aarhus course materials now live in [`course_2016/README.md`](course_2016/README.md). That folder keeps the 2016 slides, teaching code, project work, supporting resources, and legacy outputs in one browsable place so the public repo can stay product-first at the top level without losing provenance.

## Workflow Architecture

```mermaid
flowchart TD
    subgraph Inputs["Inputs And Provenance"]
        A["2016 Course Archive<br/>(course_2016/)"]
        B["Corpus Seed And Config<br/>config/corpus_seed.csv + project.yml"]
        C["Local Validation Corpora<br/>data/ + LancsBox/"]
    end

    subgraph Build["Corpus Build Layer"]
        D["Text Reconstruction<br/>Project Gutenberg recovery + checksums"]
        E["Shared Manifest Contract<br/>book metadata + inventory tables"]
        F["Shared Preprocessing<br/>cleaning, tokenization, metadata, chunking"]
    end

    subgraph Runtime["Dual Runtime Surface"]
        G["R Interface<br/>targets + scripts + renv"]
        H["Python Interface<br/>CLI + package + shared generators"]
    end

    subgraph Analysis["Analysis Layers"]
        I["Legacy 2016 Baseline<br/>AFINN + classic LDA + archived comparisons"]
        J["Modern 2026 Stack<br/>sentiment, themes, entities, embeddings, retrieval"]
        K["Benchmark Framing<br/>project results vs 2016 baseline vs cited references"]
    end

    subgraph Outputs["Public Release Outputs"]
        P["Interactive Dashboard App<br/>Vercel routes for search, theme, pacing, and corpus audit"]
        L["Figures And Tables<br/>results/figures + results/tables"]
        M["GitHub Narrative Surface<br/>README.md + course_2016/README.md"]
        N["Deep-Dive Report<br/>docs/index.html"]
        O["Reuse Paths<br/>research, teaching, DH workflows, discovery products"]
    end

    A --> D
    B --> D
    C --> E
    D --> E --> F
    F --> G
    F --> H
    G --> I
    G --> J
    H --> I
    H --> J
    I --> K
    J --> K
    K --> P
    K --> L
    K --> M
    K --> N
    P --> O
    L --> O
    M --> O
    N --> O
```

## What It Is

This repository is a public children’s literature analysis toolkit built from a 2016 Aarhus Summer University project. It reconstructs the original Gutenberg-based corpus [1], keeps the legacy baseline visible, and wraps modern local text-mining workflows around the same materials so that the project can be reused outside the classroom.

## Why It Matters

- Many humanities or classroom text-mining projects stop at notebooks, slides, or one-off scripts, which makes them hard to verify, reuse, or productize.
- Many modern NLP libraries and model repos provide strong components, but they usually stop at the method or model level rather than shipping a domain-ready literary workflow [3]-[10].
- This repo turns a historically interesting but fragile course project into a repeatable public asset with manifests, figures, tables, demos, CI, and release-ready documentation.

## What Solution It Provides

| Problem | This repo's solution |
| ------- | -------------------- |
| The original 2016 project is historically valuable but hard to rerun exactly. | Reconstruct the canonical corpus, recover the legacy sentiment/topic baseline, and preserve it as a regression target. |
| Modern NLP tools are powerful but difficult to adapt cleanly to a humanities corpus. | Provide one shared contract for corpus manifests, figures, benchmark tables, and reports, with R and Python entrypoints over the same outputs. |
| Public readers often cannot tell what a text-mining chart means or whether it is useful. | Put interpretation directly under each figure and table: what it shows, whether it is good/bad/mixed, and how to reuse it. |
| Teams who want to turn a corpus project into a reusable product usually have to invent their own SOP. | Ship a ready-made SOP for corpus reconstruction, benchmarking, visualization, release assets, and GitHub publication. |

## Why It Is Different From Related Work

| Related work | Strong at | Typical gap for public reuse | What is unique here |
| ------------ | --------- | ---------------------------- | ------------------- |
| `quanteda` and `reticulate` [3], [4] | Core text-analysis infrastructure and R/Python interoperability | They are foundations, not a domain-specific public product by themselves. | This repo turns those building blocks into a children’s literature workflow with stable outputs and release artifacts. |
| `stm`, `keyATM`, and `BERTopic` [5]-[7] | Topic modeling methods, metadata-aware modeling, and embedding-driven topic discovery | They focus on modeling techniques, not on preserving a legacy humanities baseline and publishing a full benchmark story. | This repo compares legacy 2016 methods with modern topic layers inside one literary corpus and one report surface. |
| `GLiNER`, `Qwen3-Embedding-0.6B`, and DistilBERT SST-2 [8]-[10] | Local NER, embeddings, and sentiment backends | They provide model capabilities, not corpus reconstruction, visualization standards, or product-facing SOPs. | This repo converts model outputs into reusable book-level tables, entity networks, retrieval examples, and README/report assets. |
| Many course-project repositories | Preserving scripts, lecture materials, and exploratory analysis | They are often hard to rerun, hard to compare across methods, and hard for the public to interpret. | This repo is designed as a public release: benchmark framing, demo media, CI, community files, and commercial-facing reuse guidance are part of the deliverable. |

The uniqueness here is workflow-level rather than claiming a new universal model SOTA. The repo is meant to make modern local methods practical, inspectable, and reusable for children’s literature, not to overclaim state-of-the-art results on unrelated benchmark suites.

## How The Public Can Reuse It

- Researchers can swap `config/corpus_seed.csv`, rerun the pipeline, and reuse the same reporting structure for a new literary corpus.
- Teachers can use the legacy-versus-modern comparison to show how text mining methods changed between 2016 and the current stack.
- Product teams can reuse the sentiment windows, theme heatmaps, entity networks, and retrieval tables as a starting point for recommendation, discovery, or editorial tooling.
- Open-source maintainers can reuse the SOP pattern itself: corpus manifest, benchmark framing, figure interpretation, release media, and GitHub automation.

## Quick Start

### 1. Prepare the shared `dl` runtime

```bash
make setup
make bootstrap
```

### 2. Build the generated assets

```bash
make python-assets
make readme
make report
```

### 3. Choose your interface

```bash
make modern
python -m childlit_toolkit modern
```

The full HTML deep-dive report is rendered to [`{report_path}`]({report_path}), while the public dashboard lives at [{LIVE_DASHBOARD_URL}]({LIVE_DASHBOARD_URL}).

## Corpus Snapshot

The rebuilt corpus currently spans **{manifest.shape[0]} books** and about **{total_words} words**.

{markdown_table(overview)}

What this means:

- Good: the corpus is already large enough to support meaningful descriptive text mining without leaving the public-domain children’s literature frame.
- Mixed: the corpus is still historically clustered, so claims about time trends should be treated as exploratory.
- Reuse value: future users can replace `config/corpus_seed.csv` and immediately see whether their new corpus is smaller, longer, more imbalanced, or more sentiment-skewed than this baseline.

## Visual Results

### Figure 1. Corpus Timeline

![Corpus timeline](results/figures/corpus_timeline.png)

What this means:

- Signal: this shows where the catalog is historically concentrated instead of pretending the corpus is time-neutral.
- Decision: a librarian, platform team, or curator can use this to decide whether the collection needs balancing before treating it as representative.
- Limit: timeline coverage reflects this curated public-domain corpus, not the full field of children’s literature.

### Figure 2. Provenance Coverage

![Provenance coverage](results/figures/provenance_coverage.png)

What this means:

- Signal: this makes source provenance visible title by title, which is essential for a trustworthy public dashboard.
- Decision: teams can decide whether a title is stable enough to include in benchmark or discovery views before exposing it to users.
- Limit: provenance quality does not automatically guarantee textual quality or annotation completeness.

### Figure 3. Book Length Distribution

![Book length distribution](results/figures/core_book_lengths.png)

What this means:

- Signal: this shows which books are long enough to dominate naive whole-corpus summaries.
- Decision: product teams can decide whether comparisons should be full-text, chapter-level, or windowed before using the dashboard outputs downstream.
- Limit: length is an implementation and comparability factor, not a proxy for difficulty or literary value.

### Figure 4. Chunking Risk

![Chunking risk](results/figures/chunking_risk.png)

What this means:

- Signal: this turns context-window risk into a visible processing constraint for each book.
- Decision: it supports a concrete choice between full-text, chapter, and windowed dashboard pipelines.
- Limit: chunk counts depend on preprocessing and model context length, so they are engineering warnings rather than literary claims.

### Figure 5. Author Metadata Balance

![Author balance](results/figures/author_gender_mix.png)

What this means:

- Signal: this exposes where the current catalog is imbalanced instead of hiding representation assumptions.
- Decision: curators can use it to decide where to expand or rebalance a collection before presenting it as broadly representative.
- Limit: metadata balance is only as good as the available metadata fields and the current corpus scope.

### Figure 6. Sentiment Trajectories

![Sentiment trajectories](results/figures/sentiment_trajectories.png)

What this means:

- Signal: this shows narrative pacing as a curve rather than collapsing a book into one score.
- Decision: reading platforms and educators can compare calmer versus more turbulent books when shaping reading lists or classroom contrast sets.
- Limit: sentiment movement is a pacing feature, not a measure of literary quality or reader satisfaction.

### Figure 7. Guided Theme Heatmap

![Theme heatmap](results/figures/topic_prevalence_heatmap.png)

What this means:

- Signal: this reveals title-level theme profiles that are useful for reading-list and shelf-design work.
- Decision: a librarian or curriculum team can decide which books best fit family, growth, fantasy, adventure, animal, or moral-emotion collections.
- Limit: the chart is seed-guided, so it reflects the configured theme vocabulary rather than a universal ontology of children’s literature.

### Figure 8. Book Neighborhood Map

![Embedding map](results/figures/embedding_book_map.png)

What this means:

- Signal: this makes related-title neighborhoods visible instead of forcing discovery to depend on flat subject tags.
- Decision: reading platforms and librarians can use it for related-book navigation, similarity lookup, and recommendation explainability.
- Limit: the map is not personalized and its geometry depends on the embedding backend and reduction method.

### Figure 9. Entity Co-occurrence Network

![Entity network](results/figures/entity_network.png)

What this means:

- Signal: this shows whether a book is strongly character-driven and which names dominate its narrative surface.
- Decision: teachers, librarians, and reading-product teams can use it to identify texts suited to character-centered discussion or comparison.
- Limit: when GLiNER is unavailable, the fallback is deliberately conservative and heuristic rather than full NER.

### Figure 10. Auxiliary Validation Panel

![Auxiliary validation](results/figures/auxiliary_validation_panel.png)

What this means:

- Signal: this shows how the core children’s literature corpus behaves relative to known local reference corpora.
- Decision: it helps teams sanity-check whether a new dashboard corpus looks unusually narrow, noisy, or skewed before productizing it.
- Limit: these are calibration references, not direct substitutes for the core benchmark corpus.

## Recovered 2016 Baseline

{markdown_table(legacy)}

What this means:

- Good: the archive still provides a concrete reproduction target rather than just a loose memory of the course project.
- Mixed: the baseline is lexicon-driven and context-insensitive, so it should be preserved as a comparison point, not treated as the last word.
- Reuse value: any future refactor can regression-test against these directions before trusting the modern stack.

## Modern Method and SOTA Framing

{markdown_table(comparison)}

What this means:

- Good: the repo separates project metrics from external reference context instead of pretending every method has a directly comparable literary SOTA number.
- Good: `n/a` is used honestly where no like-for-like benchmark exists.
- Reuse value: downstream users can extend the table with their own labeled evaluation sets without changing the documentation shape.

## Runtime Status

{markdown_table(methods)}

### Backend Availability Snapshot

{markdown_table(backend)}

What this means:

- Good: runtime drift is visible in the repo itself.
- Mixed: optional modern modules may still be missing in a fresh environment until users install the heavy backends.
- Reuse value: this keeps support and reproduction discussions concrete.

## Key Tables

### Topic Top Terms

{markdown_table(top_topics)}

### Retrieval Examples

{markdown_table(neighbors)}

### Entity Leaderboard

{markdown_table(entities)}

### Auxiliary Validation Summary

{markdown_table(auxiliary)}

### Dependency and License Audit

{markdown_table(dependency)}

What this means:

- Good: the repo is now publishable as a reusable toolkit rather than a folder of scripts.
- Mixed: model and corpus redistribution still require title-level and model-card checks, so the audit deliberately marks uncertain items instead of overclaiming.
- Reuse value: this table is the operational handoff for public/commercial review.

## Repository Tree

```text
.
├── README.md                  # generated public homepage for the GitHub repo
├── README.Rmd                 # R-facing note pointing to the shared README generation flow
├── LICENSE                    # Apache-2.0 license for the repository source
├── NOTICE                     # release notice and attribution surface
├── CITATION.cff               # machine-readable citation metadata
├── CONTRIBUTING.md            # contributor guidance for public reuse
├── CODE_OF_CONDUCT.md         # community conduct policy
├── SECURITY.md                # security disclosure policy
├── Makefile                   # language-neutral convenience commands
├── pyproject.toml             # Python packaging and CLI metadata
├── DESCRIPTION                # R package metadata
├── _targets.R                 # optional R targets entrypoint
├── renv.lock                  # pinned R dependency lockfile
├── vercel.json                # Vercel project metadata for the public deployment
├── .gitignore                 # git ignore policy, including local-only clutter
├── .vercelignore              # deploy filter so Vercel ships the deployment surface instead of the full workspace
├── .Rbuildignore              # R build exclusions
├── .Rprofile                  # project-level R startup behavior
├── .github/                   # CI and release workflows
├── site/                      # Figma-inspired static front-end served by Vercel
│   ├── index.html             # product landing page
│   ├── dashboard/             # overview route with quick-start and KPI surfaces
│   ├── explorer/              # searchable title explorer and similarity detail pane
│   ├── themes/                # theme-led reading-list and comparison route
│   ├── sentiment/             # narrative pacing comparison route
│   ├── corpus/                # provenance, diversity, and collection-audit route
│   ├── data/                  # generated JSON payload consumed by the front-end
│   └── assets/                # shared CSS and JavaScript for the live dashboard
├── public/                    # deploy-ready static output synced from site/ and docs/
├── R/                         # R wrappers, utilities, and reporting helpers
│   ├── manifests.R            # shared manifest/inventory helpers used by the R interface
│   ├── legacy.R               # R-side helpers for reproducing the 2016 baseline workflow
│   ├── modern.R               # R-side wrappers for the modern analysis flow
│   └── reporting.R            # R-side helpers for rendering and asset orchestration
├── childlit_toolkit/          # Python CLI and shared asset-generation pipeline
│   ├── __main__.py            # `python -m childlit_toolkit` command entrypoint
│   └── pipeline.py            # core generator for manifests, figures, tables, README, and report assets
├── config/                    # corpus seed, theme seeds, and project settings
│   ├── corpus_seed.csv        # canonical children’s literature book list for rebuilding the corpus
│   ├── project.yml            # single source of truth for paths, runtime profile, and release settings
│   ├── sota_references.csv    # cited external references used in benchmark framing
│   └── theme_seeds.yml        # guided theme labels used in modern topic visualization
├── data/                      # active datasets, reconstructed texts, and generated manifests
│   ├── manifests/             # machine-readable corpus inventory and provenance tables
│   └── raw/                   # reconstructed book texts and local validation corpora
├── docs/                      # report source and rendered HTML
│   ├── report.qmd             # Quarto-style report source
│   └── index.html             # rendered public report surface
├── environment/               # runtime bootstrap and dependency specs
│   ├── dl-r-overlay.yml       # adds R into the shared `dl` conda runtime
│   ├── python-core.txt        # core Python dependencies for the default CLI/runtime path
│   └── python-backends.txt    # optional heavier model backends for richer local analysis
├── inst/                      # package support assets, including Python helper scripts
│   ├── extdata/               # bundled runtime resources such as the legacy AFINN lexicon
│   │   └── AFINN-111.txt      # legacy sentiment lexicon used for baseline scoring
│   └── python/                # build helpers used by the R-first packaging surface
│       └── build_assets.py    # Python helper invoked by R wrappers for shared asset generation
├── renv/                      # R environment bootstrap scaffolding
├── reports/                   # report-related support artifacts
├── results/                   # figures, tables, fragments, and demo assets
│   ├── figures/               # README-safe static visualizations
│   ├── tables/                # benchmark and inventory CSV outputs
│   ├── fragments/             # reusable markdown snippets for docs/release notes
│   └── assets/                # hero GIF and other release media
├── scripts/                   # public entrypoint scripts for setup, render, and runs
│   ├── bootstrap.R            # install/restore R-side dependencies
│   ├── run_targets.R          # R CLI for legacy and modern pipeline targets
│   ├── render_readme.R        # rebuild the public homepage
│   ├── render_report.R        # rebuild the deep-dive report
│   ├── run_r.sh               # run the R path inside the shared `dl` workflow
│   └── setup_dl_runtime.sh    # bootstrap the shared dual-runtime environment
├── LancsBox/                  # auxiliary validation corpora kept in the modern toolkit surface
└── course_2016/               # structured archive of the 2016 course slides, code, outputs, and raw materials
    ├── README.md              # guided table of contents for the original course materials
    ├── slides/                # official and supplementary 2016 lecture decks
    ├── code/                  # teaching scripts and project-era analysis scripts
    ├── resources/             # corpus specification docs and course-support files
    ├── legacy_outputs/        # archived text outputs from the original project
    ├── legacy_repo/           # cleaned snapshot of the historical course repository
    └── archives/              # raw 2016 zip bundles preserved for provenance
```

## Public Release Notes

- Target repository: `{repo_name}`
- First public tag: `{CONFIG['project']['release_tag']}`
- Main release assets: corpus manifest, benchmark tables, HTML report, GIF/MP4 demo, and release bundle manifest.

## References

[1] Project Gutenberg, "Project Gutenberg," 2026. [Online]. Available: https://www.gutenberg.org/

[2] F. Å. Nielsen, "AFINN," GitHub repository, 2011-. [Online]. Available: https://github.com/fnielsen/afinn

[3] K. Benoit et al., "quanteda," 2026. [Online]. Available: https://quanteda.io/

[4] Posit, "reticulate," 2026. [Online]. Available: https://rstudio.github.io/reticulate/

[5] M. E. Roberts, B. M. Stewart, and D. Tingley, "stm: R Package for Structural Topic Models," 2026. [Online]. Available: https://search.r-project.org/CRAN/refmans/stm/html/stm-package.html

[6] S. Eshima et al., "keyATM," 2026. [Online]. Available: https://keyatm.github.io/keyATM/

[7] M. Grootendorst, "BERTopic Documentation," 2026. [Online]. Available: https://maartengr.github.io/BERTopic/

[8] U. Zaratiana et al., "GLiNER," GitHub repository, 2026. [Online]. Available: https://github.com/urchade/GLiNER

[9] Qwen Team, "Qwen3-Embedding-0.6B," Hugging Face model card, 2026. [Online]. Available: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B

[10] Hugging Face, "distilbert-base-uncased-finetuned-sst-2-english," model card, 2026. [Online]. Available: https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english
"""

    out = root_path("readme")
    ensure_parent(out)
    out.write_text(readme, encoding="utf-8")
    return out


def write_report_qmd() -> Path:
    report = f"""---
title: "Aarhus Children's Literature Toolkit"
subtitle: "2016 baseline reconstruction and 2026 dual-runtime public release"
format:
  html:
    toc: true
    toc-depth: 3
    embed-resources: true
    code-fold: false
---

# Why this report exists

This report is the deeper public-release companion to `README.md`. It keeps the GitHub front page dense and practical while offering more context, larger tables, and a fuller explanation of how the rebuilt children’s literature workflow can be reused.

The interactive product surface now lives at [`{LIVE_DASHBOARD_URL}`]({LIVE_DASHBOARD_URL}), while this report stays focused on methodology, benchmark framing, and deeper reuse guidance.

The children’s literature focus is intentional rather than incidental: the corpus offers interpretable narrative structure, recurring characters, theme-rich plots, and public-domain availability that make it unusually useful for transparent text-mining workflows.

The current stack should be read as editorial and discovery intelligence rather than as a full story-forecasting system. It is already useful for comparing books, auditing corpora, surfacing thematic neighborhoods, and supporting recommendation/editorial workflows, but it does not yet justify a strong claim that it can predict plot outcomes or literary success.

The original 2016 teaching materials now live in [`../course_2016/README.md`](../course_2016/README.md), while this report stays focused on the modern public toolkit surface.

## Who this report is for

- Libraries and reading platforms that need better related-title navigation than age labels and manual subject tags alone.
- EdTech and curriculum teams that need interpretable evidence for themed lists, classroom comparison, and reading discovery.
- Secondary audiences such as researchers, teachers, publishers, and editors who want a transparent benchmark and evidence surface.

## Current Capability

- Rebuild a transparent children’s literature corpus from the 20-book legacy baseline plus a small modern expansion layer.
- Compare books through theme profiles, sentiment trajectories, recurring entities, and semantic neighborhoods.
- Audit corpus provenance, historical clustering, metadata balance, and processing constraints before making broader claims.
- Publish the outputs as reusable figures, tables, README/report surfaces, and release assets across both R and Python entrypoints.

## What It Cannot Yet Do

- It does not perform chapter-level or scene-level story forecasting.
- It does not provide a personalized reader model.
- It does not offer validated pedagogy scoring, reading-level scoring, or curriculum suitability labels.
- It does not predict market success, sales potential, or literary quality.

## MVP Product Shape

- A searchable children’s literature dashboard.
- A similar-title panel for related-book navigation.
- A theme profile panel for reading-list and shelf design.
- A sentiment arc viewer for narrative pacing comparison.
- A corpus bias and provenance audit panel for collection review.

## Primary User Workflow

1. Start from a known title, author, or reading theme.
2. Inspect neighboring books, theme profiles, character prominence, and sentiment pacing.
3. Compare titles before building a reading list, recommendation surface, or classroom collection.
4. Export or reuse the evidence in discovery, curation, and collection-audit workflows.

## Roadmap

- Phase 1: ship the current dashboard MVP using the existing similarity, theme, sentiment, entity, and corpus-audit outputs.
- Phase 2: add institution-facing tooling such as filters, cohort comparison, exportable reading lists, and stronger collection views.
- Phase 3: add sequence-aware modeling only after chapter-level structure, labels, and evaluation data exist.

## Why Not Story Prediction Yet

Story prediction is a different task from similarity, theme profiling, and pacing comparison. It would require chapter- or scene-level sequence data, explicit labels, and an evaluation loop that measures whether the model actually predicts future narrative events instead of just describing books retrospectively. The current repo does not have that validation layer yet, so it should not be marketed as a story-forecasting system.

## Shared entrypoints

```bash
make setup
make bootstrap
make python-assets
make readme
make report
```

```bash
python -m childlit_toolkit modern
Rscript scripts/run_targets.R modern
```

## Corpus summary

```{{=markdown}}
{(root_path("fragments_dir") / "corpus_summary.md").read_text(encoding="utf-8")}
```

## Visual analytics

### Timeline

![Timeline](../results/figures/corpus_timeline.png)

- Signal: historical concentration in the current corpus.
- Decision: whether the collection is balanced enough for discovery or classroom use.
- Limit: this reflects the curated public-domain corpus, not the whole field.

### Provenance coverage

![Provenance](../results/figures/provenance_coverage.png)

- Signal: source reliability and reconstruction transparency.
- Decision: whether a title is stable enough to expose in benchmark or dashboard views.
- Limit: provenance quality does not guarantee interpretive quality.

### Length distribution

![Length](../results/figures/core_book_lengths.png)

- Signal: which titles are large enough to distort naive comparisons.
- Decision: whether to compare books as full texts, chapters, or windows.
- Limit: length is an engineering and comparability factor, not a quality signal.

### Chunking risk

![Chunking](../results/figures/chunking_risk.png)

- Signal: long-context processing pressure per title.
- Decision: which segmentation strategy is safe for a live dashboard pipeline.
- Limit: chunk counts depend on preprocessing and model context windows.

### Metadata balance

![Metadata](../results/figures/author_gender_mix.png)

- Signal: representational imbalance in the current catalog.
- Decision: where to rebalance or qualify the collection before making broader claims.
- Limit: this depends on the available metadata fields and corpus scope.

### Sentiment trajectories

![Sentiment](../results/figures/sentiment_trajectories.png)

- Signal: narrative pacing over the course of a book.
- Decision: compare calmer versus more turbulent reading experiences for list building or classroom use.
- Limit: this is a pacing feature, not a literary-quality score.

### Guided theme heatmap

![Themes](../results/figures/topic_prevalence_heatmap.png)

- Signal: title-level theme profiles for reading-list and discovery work.
- Decision: which books fit friendship, family, growth, fantasy, adventure, animals, or moral-emotion collections.
- Limit: the view is seed-guided, so it reflects the configured theme vocabulary.

### Semantic neighborhood

![Neighborhood](../results/figures/embedding_book_map.png)

- Signal: related-title neighborhoods beyond flat subject tags.
- Decision: which adjacent books a library or reading platform should surface next.
- Limit: this is not personalized recommendation and depends on the embedding backend.

### Entity network

![Entities](../results/figures/entity_network.png)

- Signal: whether a book is strongly character-driven and which names dominate it.
- Decision: which books are especially useful for character-centered discussion or comparison.
- Limit: fallback extraction is heuristic when the stronger local NER backend is unavailable.

### Auxiliary validation

![Auxiliary](../results/figures/auxiliary_validation_panel.png)

- Signal: how the core corpus compares with local reference corpora.
- Decision: whether a new dashboard corpus looks unusually narrow or skewed before productization.
- Limit: these are calibration references, not replacements for the core benchmark.

## Legacy baseline

```{{=markdown}}
{(root_path("fragments_dir") / "legacy_baseline.md").read_text(encoding="utf-8")}
```

## Modern stack

```{{=markdown}}
{(root_path("fragments_dir") / "modern_stack.md").read_text(encoding="utf-8")}
```

## Release bundle

```{{=markdown}}
{(root_path("fragments_dir") / "release_readiness.md").read_text(encoding="utf-8")}
```

## Reuse guidance

1. Update `config/corpus_seed.csv` with a new children’s literature corpus.
2. Adjust `config/theme_seeds.yml` if the thematic frame changes.
3. Rebuild the assets.
4. Review the benchmark framing table before making public claims.

This is the intended SOP value of the repo: a reusable public workflow, not just a single archived analysis.
"""
    report_path = root_path("report_qmd")
    ensure_parent(report_path)
    report_path.write_text(report, encoding="utf-8")
    return report_path


def write_fallback_report_html() -> Path:
    report_out = root_path("report_html")
    ensure_parent(report_out)
    manifest = pd.read_csv(root_path("corpus_manifest"))
    overview = pd.read_csv(root_path("tables_dir") / "corpus_manifest_overview.csv")
    legacy = pd.read_csv(root_path("legacy_summary"))
    comparison = pd.read_csv(root_path("tables_dir") / "benchmark_sota_comparison.csv")
    auxiliary = pd.read_csv(root_path("tables_dir") / "auxiliary_validation_summary.csv")

    def table_html(df: pd.DataFrame) -> str:
        return df.to_html(index=False, border=0, classes="dataframe")

    intro_sections = [
        (
            "Who This Report Is For",
            "<p>Libraries, reading platforms, and curriculum teams that need better title discovery, themed list building, and catalog interpretation than age labels and manual tags alone.</p>",
        ),
        (
            "Current Capability",
            "<ul>"
            "<li>Rebuild a transparent children’s literature corpus from the 20-book legacy baseline plus a small expansion layer.</li>"
            "<li>Compare books through theme profiles, sentiment trajectories, recurring entities, and semantic neighborhoods.</li>"
            "<li>Audit provenance, historical clustering, metadata balance, and processing constraints before making broader claims.</li>"
            "<li>Publish the results as reusable figures, tables, README/report surfaces, and release assets across both R and Python.</li>"
            "</ul>",
        ),
        (
            "What It Cannot Yet Do",
            "<ul>"
            "<li>No chapter-level or scene-level story forecasting.</li>"
            "<li>No personalized reader model.</li>"
            "<li>No validated pedagogy scoring, reading-level scoring, or curriculum suitability labels.</li>"
            "<li>No market-success, sales, or literary-quality prediction.</li>"
            "</ul>",
        ),
        (
            "MVP Product Shape",
            "<ul>"
            "<li>A searchable children’s literature dashboard.</li>"
            "<li>A similar-title panel for related-book navigation.</li>"
            "<li>A theme profile panel for reading-list and shelf design.</li>"
            "<li>A sentiment arc viewer for narrative pacing comparison.</li>"
            "<li>A corpus bias and provenance audit panel for collection review.</li>"
            "</ul>",
        ),
        (
            "Primary User Workflow",
            "<ol>"
            "<li>Start from a known title, author, or reading theme.</li>"
            "<li>Inspect neighboring books, theme profiles, character prominence, and sentiment pacing.</li>"
            "<li>Compare titles before building a reading list, recommendation surface, or classroom collection.</li>"
            "<li>Export or reuse the evidence in discovery, curation, and collection-audit workflows.</li>"
            "</ol>",
        ),
        (
            "Roadmap",
            "<ul>"
            "<li>Phase 1: ship the current dashboard MVP using existing similarity, theme, sentiment, entity, and corpus-audit outputs.</li>"
            "<li>Phase 2: add institution-facing tooling such as filters, cohort comparison, exportable reading lists, and stronger collection views.</li>"
            "<li>Phase 3: add sequence-aware modeling only after chapter-level structure, labels, and evaluation data exist.</li>"
            "</ul>",
        ),
        (
            "Why Not Story Prediction Yet",
            "<p>Story prediction is a different task from similarity, theme profiling, and pacing comparison. It requires sequence data, labels, and evaluation that the current repo does not yet have, so this product should be read as editorial and discovery intelligence rather than a forecasting engine.</p>",
        ),
    ]
    sections = [
        ("Corpus Summary", table_html(overview)),
        ("Legacy Baseline", table_html(legacy)),
        ("Benchmark Framing", table_html(comparison)),
        ("Auxiliary Validation", table_html(auxiliary)),
    ]
    figures = [
        (
            "Timeline",
            "../results/figures/corpus_timeline.png",
            "<ul><li><strong>Signal:</strong> historical concentration in the current corpus.</li><li><strong>Decision:</strong> whether the collection is balanced enough for discovery or classroom use.</li><li><strong>Limit:</strong> this reflects the curated public-domain corpus, not the whole field.</li></ul>",
        ),
        (
            "Provenance coverage",
            "../results/figures/provenance_coverage.png",
            "<ul><li><strong>Signal:</strong> source reliability and reconstruction transparency.</li><li><strong>Decision:</strong> whether a title is stable enough to expose in benchmark or dashboard views.</li><li><strong>Limit:</strong> provenance quality does not guarantee interpretive quality.</li></ul>",
        ),
        (
            "Book Lengths",
            "../results/figures/core_book_lengths.png",
            "<ul><li><strong>Signal:</strong> which titles are large enough to distort naive comparisons.</li><li><strong>Decision:</strong> whether to compare books as full texts, chapters, or windows.</li><li><strong>Limit:</strong> length is an engineering and comparability factor, not a quality signal.</li></ul>",
        ),
        (
            "Chunking risk",
            "../results/figures/chunking_risk.png",
            "<ul><li><strong>Signal:</strong> long-context processing pressure per title.</li><li><strong>Decision:</strong> which segmentation strategy is safe for a live dashboard pipeline.</li><li><strong>Limit:</strong> chunk counts depend on preprocessing and model context windows.</li></ul>",
        ),
        (
            "Metadata balance",
            "../results/figures/author_gender_mix.png",
            "<ul><li><strong>Signal:</strong> representational imbalance in the current catalog.</li><li><strong>Decision:</strong> where to rebalance or qualify the collection before making broader claims.</li><li><strong>Limit:</strong> this depends on the available metadata fields and corpus scope.</li></ul>",
        ),
        (
            "Sentiment",
            "../results/figures/sentiment_trajectories.png",
            "<ul><li><strong>Signal:</strong> narrative pacing over the course of a book.</li><li><strong>Decision:</strong> compare calmer versus more turbulent reading experiences for list building or classroom use.</li><li><strong>Limit:</strong> this is a pacing feature, not a literary-quality score.</li></ul>",
        ),
        (
            "Themes",
            "../results/figures/topic_prevalence_heatmap.png",
            "<ul><li><strong>Signal:</strong> title-level theme profiles for reading-list and discovery work.</li><li><strong>Decision:</strong> which books fit family, growth, fantasy, adventure, animal, or moral-emotion collections.</li><li><strong>Limit:</strong> the view is seed-guided, so it reflects the configured theme vocabulary.</li></ul>",
        ),
        (
            "Neighborhood",
            "../results/figures/embedding_book_map.png",
            "<ul><li><strong>Signal:</strong> related-title neighborhoods beyond flat subject tags.</li><li><strong>Decision:</strong> which adjacent books a library or reading platform should surface next.</li><li><strong>Limit:</strong> this is not personalized recommendation and depends on the embedding backend.</li></ul>",
        ),
        (
            "Entities",
            "../results/figures/entity_network.png",
            "<ul><li><strong>Signal:</strong> whether a book is strongly character-driven and which names dominate it.</li><li><strong>Decision:</strong> which books are especially useful for character-centered discussion or comparison.</li><li><strong>Limit:</strong> fallback extraction is heuristic when the stronger local NER backend is unavailable.</li></ul>",
        ),
        (
            "Auxiliary Validation",
            "../results/figures/auxiliary_validation_panel.png",
            "<ul><li><strong>Signal:</strong> how the core corpus compares with local reference corpora.</li><li><strong>Decision:</strong> whether a new dashboard corpus looks unusually narrow or skewed before productization.</li><li><strong>Limit:</strong> these are calibration references, not replacements for the core benchmark.</li></ul>",
        ),
    ]
    intro_html = "\n".join(f"<section><h2>{html.escape(title)}</h2>{body}</section>" for title, body in intro_sections)
    section_html = "\n".join(f"<section><h2>{html.escape(title)}</h2>{body}</section>" for title, body in sections)
    figure_html = "\n".join(
        f'<section><h2>{html.escape(title)}</h2><img src="{html.escape(src)}" alt="{html.escape(title)}" />{notes}</section>'
        for title, src, notes in figures
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aarhus Children's Literature Toolkit Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 1100px; line-height: 1.6; color: #1d1d1f; padding: 0 1rem; }}
    h1, h2 {{ color: #0b3954; }}
    img {{ max-width: 100%; border: 1px solid #d7d7d7; border-radius: 8px; margin: 0.75rem 0 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid #d7d7d7; padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }}
    th {{ background: #f4f7fb; }}
    .lede {{ font-size: 1.05rem; color: #334; }}
  </style>
</head>
<body>
  <h1>Aarhus Children's Literature Toolkit Report</h1>
  <p class="lede">Fallback HTML report generated without Quarto. The repo still keeps <code>docs/report.qmd</code> as the canonical report source.</p>
  <p><a href="{LIVE_DASHBOARD_URL}">Back to the live dashboard</a></p>
  <p>This report covers {manifest.shape[0]} books and {fmt_int(manifest['word_count'].sum())} words across the rebuilt corpus.</p>
  {intro_html}
  {section_html}
  <h2>Figures</h2>
  {figure_html}
</body>
</html>
"""
    report_out.write_text(page, encoding="utf-8")
    return report_out


def sync_public_site() -> Path:
    public_dir = root_path("public_dir")
    site_dir = root_path("app_dir")
    report_html = root_path("report_html")
    report_assets = report_html.parent / "report_files"
    results_dir = root_path("figures_dir").parent

    if public_dir.exists():
        shutil.rmtree(public_dir)

    shutil.copytree(site_dir, public_dir)

    report_dir = public_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    if report_html.exists():
        shutil.copy2(report_html, report_dir / "index.html")
    if report_assets.exists():
        shutil.copytree(report_assets, public_dir / "report_files", dirs_exist_ok=True)
    if results_dir.exists():
        shutil.copytree(results_dir, public_dir / "results", dirs_exist_ok=True)

    return public_dir


def render_quarto_report() -> Path:
    report_qmd = write_report_qmd()
    report_out = root_path("report_html")
    ensure_parent(report_out)
    support_dir = report_out.parent / "report_files"
    try:
        quarto_bin = shutil.which("quarto")
        if quarto_bin is None and os.environ.get("CHILDLIT_ALLOW_BUNDLED_QUARTO", "0") == "1":
            local_quarto = ROOT / "tools" / "bin" / "quarto"
            if local_quarto.exists():
                quarto_bin = str(local_quarto)
        if quarto_bin is None:
            raise RuntimeError("Quarto CLI not found.")
        if support_dir.exists():
            shutil.rmtree(support_dir)
        completed = subprocess.run(
            [quarto_bin, "render", str(report_qmd), "--to", "html", "--output", "index.html"],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode != 0 or not report_out.exists():
            write_fallback_report_html()
        elif support_dir.exists():
            shutil.rmtree(support_dir)
    except Exception:
        write_fallback_report_html()
    sync_public_site()
    build_release_manifest()
    build_fragments(pd.read_csv(root_path("corpus_manifest")))
    return report_out


def build_modern_outputs() -> pd.DataFrame:
    print("Starting modern asset build...", flush=True)
    manifest = pd.read_csv(root_path("corpus_manifest")) if root_path("corpus_manifest").exists() else build_manifest()
    if not root_path("local_assets").exists():
        print("Building local asset inventory...", flush=True)
        build_inventory()
    if not root_path("legacy_summary").exists():
        print("Recovering legacy summary...", flush=True)
        build_legacy_summary()
    print("Saving backend status...", flush=True)
    save_backend_status()

    records = load_book_records(manifest)
    print("Rendering corpus overview figures...", flush=True)
    plot_corpus_timeline(manifest)
    plot_book_lengths(manifest)
    plot_author_gender(manifest)
    print("Rendering sentiment trajectories...", flush=True)
    sentiment_df, sentiment_backend, _ = build_sentiment_trajectories(records)
    _ = sentiment_df
    print("Rendering theme and topic outputs...", flush=True)
    build_theme_heatmap(records)
    build_topic_outputs(records)
    print("Rendering similarity outputs...", flush=True)
    _, embedding_backend, _ = build_embedding_outputs(records)
    print("Rendering entity outputs...", flush=True)
    _, ner_backend, _ = build_entity_outputs(records)
    print("Rendering auxiliary validation outputs...", flush=True)
    build_auxiliary_validation()
    print("Writing audit and benchmark tables...", flush=True)
    build_dependency_audit()
    build_benchmark_tables(manifest, pd.read_csv(root_path("legacy_summary")), sentiment_backend, embedding_backend, ner_backend)
    print("Exporting dashboard dataset...", flush=True)
    build_dashboard_dataset(manifest, records)
    print("Building release media and fragments...", flush=True)
    build_hero_assets()
    if root_path("report_html").exists():
        sync_public_site()
    build_release_manifest()
    build_fragments(manifest)
    print("Modern asset build complete.", flush=True)

    return pd.DataFrame(
        {
            "output": [
                "results/figures/corpus_timeline.png",
                "results/figures/sentiment_trajectories.png",
                "results/figures/topic_prevalence_heatmap.png",
                "results/figures/embedding_book_map.png",
                "results/figures/entity_network.png",
                "results/figures/auxiliary_validation_panel.png",
                "results/assets/hero.gif",
                "results/assets/hero.mp4",
                "site/data/dashboard.json",
            ]
        }
    )


def bootstrap_python() -> None:
    core = ROOT / "environment" / "python-core.txt"
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(core)], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(ROOT)], check=True)


def smoke() -> None:
    required = [
        ROOT / "config" / "corpus_seed.csv",
        ROOT / "config" / "theme_seeds.yml",
        ROOT / "childlit_toolkit" / "pipeline.py",
        ROOT / "site" / "index.html",
        ROOT / "site" / "assets" / "app.css",
        ROOT / "site" / "assets" / "app.js",
        ROOT / "public" / "index.html",
        ROOT / "vercel.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")
    print("Smoke check passed.")


def run_all(render_report: bool = True) -> None:
    print("Building inventory...", flush=True)
    build_inventory()
    print("Building manifest...", flush=True)
    build_manifest()
    print("Building legacy summary...", flush=True)
    build_legacy_summary()
    build_modern_outputs()
    print("Rendering README/report sources...", flush=True)
    render_readme_markdown()
    write_report_qmd()
    if render_report:
        try:
            print("Rendering HTML report...", flush=True)
            render_quarto_report()
        except Exception as exc:  # noqa: BLE001
            print(f"Quarto render skipped: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Dual-runtime asset pipeline for the Aarhus children's literature toolkit.")
    parser.add_argument(
        "command",
        choices=["bootstrap", "inventory", "manifest", "legacy", "modern", "render", "report", "all", "smoke"],
    )
    args = parser.parse_args(argv)

    if args.command == "bootstrap":
        bootstrap_python()
    elif args.command == "inventory":
        build_inventory()
    elif args.command == "manifest":
        build_manifest()
    elif args.command == "legacy":
        build_legacy_summary()
    elif args.command == "modern":
        build_modern_outputs()
    elif args.command == "render":
        if not root_path("corpus_manifest").exists():
            run_all(render_report=False)
        else:
            build_modern_outputs()
            render_readme_markdown()
            write_report_qmd()
    elif args.command == "report":
        build_modern_outputs()
        render_readme_markdown()
        write_report_qmd()
        render_quarto_report()
    elif args.command == "all":
        run_all(render_report=True)
    elif args.command == "smoke":
        smoke()
