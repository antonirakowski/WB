"""
Analysis pipeline for the telephone game experiment.
Reuses metric functions from analysis.py.
Key new metric: semantic drift per hop (cosine distance from original message).
Output: results_telephone/report.md, results_telephone/plots/*.png
"""

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import spacy
import ollama
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Reuse metric functions from analysis.py
from analysis import (
    sentiment_metrics,
    topic_drift,
    distinct1,
    llm_judge,
    lemmatize,
    tokenize_surface,
    EDUCATION_KEYWORDS,
    CONFLICT_KEYWORDS,
    JUDGE_SYSTEM,
    MODEL_SHORT,
    PAIR_SHORT,
)

RESULTS_DIR = Path("results_telephone")
PLOTS_DIR = RESULTS_DIR / "plots"


# ── Load ──────────────────────────────────────────────────────────────────────

def load_results() -> pd.DataFrame:
    rows = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        for hop in data["chain"]:
            rows.append({
                "model": data["model"],
                "pair": data["pair"],
                "pair_label": data["pair_label"],
                "original_message": data["original_message"],
                "hop": hop["hop"],
                "agent_id": hop["agent_id"],
                "name": hop["name"],
                "received": hop["received"],
                "text": hop["text"],
                "elapsed_s": hop.get("elapsed_s", 0),
            })
    return pd.DataFrame(rows)


# ── Semantic drift ────────────────────────────────────────────────────────────

def compute_drift_per_chain(data: dict, sbert) -> list[float]:
    """Cosine distance from original message at each hop."""
    original = data["original_message"]
    texts = [hop["text"] for hop in data["chain"]]
    all_texts = [original] + texts
    embs = sbert.encode(all_texts, show_progress_bar=False)
    orig_emb = embs[0]
    dists = []
    for emb in embs[1:]:
        d = 1 - float(np.dot(orig_emb, emb) /
                      (np.linalg.norm(orig_emb) * np.linalg.norm(emb) + 1e-10))
        dists.append(d)
    return dists


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_drift_curves(drift_data: dict):
    """drift_data: {pair: {model: [dist_hop0, dist_hop1, ...]}}"""
    pairs = list(drift_data.keys())
    fig, axes = plt.subplots(1, len(pairs), figsize=(5 * len(pairs), 4), sharey=True)
    if len(pairs) == 1:
        axes = [axes]

    for ax, pair in zip(axes, pairs):
        for model, dists in drift_data[pair].items():
            hops = list(range(1, len(dists) + 1))
            ax.plot(hops, dists, marker="o",
                    label=MODEL_SHORT.get(model, model), alpha=0.85, linewidth=1.5)
        ax.set_title(PAIR_SHORT.get(pair, pair), fontsize=11)
        ax.set_xlabel("Hop #")
        ax.set_ylim(0, 1)
        # shade A vs B hops
        for i in range(len(dists)):
            color = "steelblue" if i % 2 == 0 else "tomato"
            ax.axvspan(i + 0.5, i + 1.5, alpha=0.06, color=color)
        ax.legend(fontsize=7)

    axes[0].set_ylabel("Cosine distance from original")
    fig.suptitle("Semantic Drift per Hop  (blue=Agent A hop, red=Agent B hop)",
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "drift_curves.png", dpi=150)
    plt.close()


def plot_drift_by_agent(df: pd.DataFrame):
    """Compare mean drift caused by A-hops vs B-hops per model."""
    df_a = df[df["hop"] % 2 == 0].groupby("model")["drift"].mean().rename("Agent A")
    df_b = df[df["hop"] % 2 == 1].groupby("model")["drift"].mean().rename("Agent B")
    combined = pd.concat([df_a, df_b], axis=1)
    combined.index = [MODEL_SHORT.get(m, m) for m in combined.index]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(combined))
    w = 0.35
    ax.bar(x - w/2, combined["Agent A"], w, label="Agent A hops", color="steelblue")
    ax.bar(x + w/2, combined["Agent B"], w, label="Agent B hops", color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels(combined.index, rotation=15)
    ax.set_ylabel("Mean cosine distance from original")
    ax.set_title("Drift caused by Agent A vs Agent B hops")
    ax.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "drift_by_agent.png", dpi=150)
    plt.close()


def plot_drift_heatmap(df: pd.DataFrame):
    piv = df.groupby(["model", "pair"])["drift"].mean().unstack().rename(
        index=MODEL_SHORT, columns=PAIR_SHORT)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    sns.heatmap(piv, annot=True, fmt=".3f", cmap="YlOrRd", ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title("Mean Semantic Drift per Chain  (↑ = more distortion)", fontsize=12, pad=10)
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "drift_heatmap.png", dpi=150)
    plt.close()


def plot_sentiment_evolution(df: pd.DataFrame):
    pairs = df["pair"].unique()
    fig, axes = plt.subplots(1, len(pairs), figsize=(5 * len(pairs), 4), sharey=True)
    if len(pairs) == 1:
        axes = [axes]
    for ax, pair in zip(axes, pairs):
        sub = df[df["pair"] == pair]
        for model, grp in sub.groupby("model"):
            by_hop = grp.groupby("hop")["mean_compound"].mean()
            ax.plot(by_hop.index, by_hop.values, marker="o",
                    label=MODEL_SHORT.get(model, model), alpha=0.85)
        ax.set_title(PAIR_SHORT.get(pair, pair), fontsize=11)
        ax.set_xlabel("Hop #")
        ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("Mean VADER compound")
    fig.suptitle("Sentiment Evolution across Hops", fontsize=12)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "sentiment_evolution.png", dpi=150)
    plt.close()


def _heatmap(pivot, title, fname, cmap="YlOrRd", fmt=".2f"):
    pivot = pivot.rename_axis(None, axis=0).rename_axis(None, axis=1)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    sns.heatmap(pivot, annot=True, fmt=fmt, cmap=cmap, ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / fname, dpi=150)
    plt.close()


# ── Report ────────────────────────────────────────────────────────────────────

def generate_report(df: pd.DataFrame, df_summary: pd.DataFrame,
                    worst: list[dict]) -> str:
    L = []
    L.append("# Telephone Game Report: Message Distortion across Conflicting Personas\n")

    L.append("## Design\n")
    L.append(
        "A neutral factual message about a historical conflict passes through a chain "
        "of 6 agents alternating between conflicting group personas (A→B→A→B→A→B). "
        "Each agent restates the received message *in their own words, as someone with "
        "their background would understand it*. No bias is instructed — distortion "
        "emerges (or not) from the model's latent priors.\n"
    )
    L.append("### Starting messages\n")
    for pair, msg in df.groupby("pair")["original_message"].first().items():
        L.append(f"**{PAIR_SHORT.get(pair, pair)}:** {msg}\n")

    L.append("## Overview\n")
    L.append("| Model | Pair | Mean Drift | Final Drift | Avg Sentiment | Distinct-1 |")
    L.append("|-------|------|:----------:|:-----------:|:-------------:|:----------:|")
    for _, r in df_summary.sort_values(["model", "pair"]).iterrows():
        L.append(
            f"| {r['model']} | {r['pair_label']} "
            f"| {r.get('mean_drift', 0):.3f} "
            f"| {r.get('final_drift', 0):.3f} "
            f"| {r.get('mean_compound', 0):.3f} "
            f"| {r.get('distinct1', 0):.3f} |"
        )

    L.append("\n## Semantic Drift per Hop\n")
    L.append(
        "Cosine distance from the original message at each hop. "
        "Blue shading = Agent A hops, red = Agent B hops.\n"
    )
    L.append("![Drift curves](plots/drift_curves.png)\n")
    L.append("![Drift heatmap](plots/drift_heatmap.png)\n")

    L.append("## Drift by Agent Group\n")
    L.append("Which group's hops cause larger distortions on average?\n")
    L.append("![Drift by agent](plots/drift_by_agent.png)\n")

    L.append("## Sentiment Evolution\n")
    L.append("How VADER compound score changes across hops.\n")
    L.append("![Sentiment evolution](plots/sentiment_evolution.png)\n")

    L.append("## Distinct-1 per Hop Agent\n")
    L.append("![Distinct-1 heatmap](plots/distinct1_heatmap.png)\n")

    if "hostility" in df.columns:
        L.append("## LLM Judge Scores\n")
        for metric in ["hostility", "stereotyping", "topic_adherence"]:
            L.append(f"### {metric.replace('_', ' ').title()}\n")
            L.append(f"![{metric}](plots/judge_{metric}_heatmap.png)\n")

    L.append("## Worst Sentences by Sentiment\n")
    L.append("| Model | Pair | Hop | Agent | Score | Sentence |")
    L.append("|-------|------|:---:|-------|------:|----------|")
    for w in worst[:20]:
        sent = w["sentence"].replace("|", "\\|").replace("\n", " ")
        if len(sent) > 250:
            sent = sent[:247] + "…"
        L.append(
            f"| {w['model']} | {w['pair']} | {w['hop']} "
            f"| {w['agent_id']} | {w['score']:.3f} | {sent} |"
        )

    return "\n".join(L) + "\n"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading results...")
    df = load_results()
    print(f"  {len(df)} hops across {df.groupby(['model','pair']).ngroups} chains\n")

    print("Loading NLP models...")
    nlp = spacy.load("en_core_web_sm")
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()
    sbert = SentenceTransformer("all-MiniLM-L6-v2")

    # ── Semantic drift (per chain) ──
    print("Computing semantic drift...")
    drift_lookup: dict = {}  # (model, pair, hop) → drift
    drift_data: dict = {}    # for plot: {pair: {model: [dists]}}

    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        model, pair = data["model"], data["pair"]
        dists = compute_drift_per_chain(data, sbert)
        drift_data.setdefault(pair, {})[model] = dists
        for hop_idx, d in enumerate(dists):
            drift_lookup[(model, pair, hop_idx)] = d

    df["drift"] = df.apply(
        lambda r: drift_lookup.get((r["model"], r["pair"], r["hop"]), np.nan), axis=1
    )

    # ── Per-hop sentiment + topic drift ──
    print("Computing per-hop metrics...")
    sent_rows, drift_rows, worst_sentences = [], [], []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="  hops"):
        text, pair = row["text"], row["pair"]

        s = sentiment_metrics(text, vader)
        sent_rows.append({
            "model": row["model"], "pair": pair,
            "hop": row["hop"], "agent_id": row["agent_id"],
            "mean_compound": s["mean_compound"], "neg_count": s["neg_count"],
        })
        for sentence, score in s["all_scores"]:
            worst_sentences.append({
                "model": row["model"], "pair": pair,
                "hop": row["hop"], "agent_id": row["agent_id"],
                "score": score, "sentence": sentence,
            })

        lemmas = lemmatize(text, nlp)
        td = topic_drift(lemmas, pair)
        drift_rows.append({
            "model": row["model"], "pair": pair,
            "hop": row["hop"], "agent_id": row["agent_id"],
            **td,
        })

    df = df.merge(pd.DataFrame(sent_rows),
                  on=["model", "pair", "hop", "agent_id"], how="left")
    df = df.merge(pd.DataFrame(drift_rows),
                  on=["model", "pair", "hop", "agent_id"], how="left")
    worst_sentences.sort(key=lambda x: x["score"])

    # ── Per-chain summary ──
    print("Computing per-chain summary...")
    summary_rows = []
    for (model, pair), grp in df.groupby(["model", "pair"]):
        meta = grp.iloc[0]
        final_drift = grp.sort_values("hop").iloc[-1]["drift"]
        summary_rows.append({
            "model": model,
            "pair": pair,
            "pair_label": meta["pair_label"],
            "mean_drift": grp["drift"].mean(),
            "final_drift": final_drift,
            "mean_compound": grp["mean_compound"].mean(),
            "distinct1": distinct1(grp["text"].tolist()),
        })
    df_summary = pd.DataFrame(summary_rows)

    # ── LLM judge (skip if cached) ──
    judge_cols = ["hostility", "stereotyping", "topic_adherence"]
    cache_path = RESULTS_DIR / "metrics.csv"
    merge_keys = ["model", "pair", "hop", "agent_id"]
    if cache_path.exists():
        cached = pd.read_csv(cache_path)
        if all(c in cached.columns for c in judge_cols):
            print("Loading LLM judge scores from cache (skipping re-run)...")
            df_judge = cached[merge_keys + judge_cols].drop_duplicates(merge_keys)
            df = df.merge(df_judge, on=merge_keys, how="left")
        else:
            print("Running LLM judge...")
            judge_rows = []
            for _, row in tqdm(df.iterrows(), total=len(df), desc="  judge"):
                scores = llm_judge(row["text"])
                judge_rows.append({"model": row["model"], "pair": row["pair"],
                                   "hop": row["hop"], "agent_id": row["agent_id"], **scores})
            df = df.merge(pd.DataFrame(judge_rows), on=merge_keys, how="left")
    else:
        print("Running LLM judge...")
        judge_rows = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="  judge"):
            scores = llm_judge(row["text"])
            judge_rows.append({"model": row["model"], "pair": row["pair"],
                               "hop": row["hop"], "agent_id": row["agent_id"], **scores})
        df = df.merge(pd.DataFrame(judge_rows), on=merge_keys, how="left")

    # ── Save ──
    print("Saving CSVs...")
    df.to_csv(RESULTS_DIR / "metrics.csv", index=False)
    df_summary.to_csv(RESULTS_DIR / "summary.csv", index=False)

    # ── Plots ──
    print("Generating plots...")
    plot_drift_curves(drift_data)
    plot_drift_heatmap(df)
    plot_drift_by_agent(df)
    plot_sentiment_evolution(df)

    _heatmap(
        df.groupby(["model", "pair"])["distinct1_per_hop"].mean().unstack().rename(
            index=MODEL_SHORT, columns=PAIR_SHORT)
        if "distinct1_per_hop" in df.columns else
        df_summary.pivot_table(index="model", columns="pair", values="distinct1").rename(
            index=MODEL_SHORT, columns=PAIR_SHORT),
        "Distinct-1 per Chain  (↑ = more lexically diverse)",
        "distinct1_heatmap.png", cmap="Blues",
    )

    for metric, cmap in [("hostility", "YlOrRd"), ("stereotyping", "YlOrRd"),
                          ("topic_adherence", "YlGn")]:
        if metric in df.columns:
            _heatmap(
                df.groupby(["model", "pair"])[metric].mean().unstack().rename(
                    index=MODEL_SHORT, columns=PAIR_SHORT),
                f"LLM Judge — {metric.replace('_', ' ').title()}",
                f"judge_{metric}_heatmap.png", cmap=cmap,
            )

    # ── Report ──
    print("Generating report.md...")
    report = generate_report(df, df_summary, worst_sentences)
    (RESULTS_DIR / "report.md").write_text(report, encoding="utf-8")

    print("\n✓ Done")
    print(f"  {RESULTS_DIR / 'report.md'}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        RESULTS_DIR = Path(sys.argv[1])
        PLOTS_DIR = RESULTS_DIR / "plots"
    main()
