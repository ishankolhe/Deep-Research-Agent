import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.gemini_client import generate_json
from utils.image_client import find_image, download_image

ACCENT = "#2E3192"
ACCENT_LIGHT = "#6C6FC4"
PALETTE = ["#2E3192", "#1DA1A3", "#E8863B", "#8B5CF6", "#D64550"]


def extract_chartable_data(research_results: list[dict]) -> list[dict]:
    """
    Asks Gemini to find any numeric comparisons/trends in the gathered facts that
    would make a good simple chart. Returns a list of chart specs:
    [{"title": ..., "type": "bar"|"line", "labels": [...], "values": [...], "y_label": ...}]
    """
    all_facts = []
    for r in research_results:
        all_facts.extend(f["text"] for f in r["facts"])
    facts_text = "\n".join(f"- {t}" for t in all_facts)

    prompt = (
        f"Here are facts gathered during research:\n{facts_text}\n\n"
        f"Identify up to 3 sets of numeric data suitable for a simple bar or line chart "
        f"(e.g. a comparison across categories, or a trend over time). Only include "
        f"charts where real numbers were present in the facts above — do not invent data. "
        f"If none exist, return an empty list."
    )
    schema = (
        '[{"title": "chart title", "type": "bar", "labels": ["A","B"], '
        '"values": [1.0, 2.0], "y_label": "units"}]'
    )
    try:
        specs = generate_json(prompt, schema)
    except Exception:
        specs = []
    return specs if isinstance(specs, list) else []


def render_charts(chart_specs: list[dict], output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    plt.rcParams.update({
        "font.size": 11,
        "axes.edgecolor": "#D0D0D8",
        "axes.labelcolor": "#333333",
        "text.color": "#222222",
        "xtick.color": "#444444",
        "ytick.color": "#444444",
    })
    paths = []
    for i, spec in enumerate(chart_specs):
        try:
            fig, ax = plt.subplots(figsize=(6.4, 4), dpi=150)
            labels = spec.get("labels", [])
            values = spec.get("values", [])
            colors = [PALETTE[j % len(PALETTE)] for j in range(len(labels))]

            if spec.get("type") == "line":
                ax.plot(labels, values, marker="o", color=ACCENT, linewidth=2.5,
                        markersize=7, markerfacecolor=ACCENT_LIGHT)
                ax.fill_between(range(len(labels)), values, alpha=0.08, color=ACCENT)
            else:
                bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="none")
                for b in bars:
                    h = b.get_height()
                    ax.annotate(f"{h:g}", (b.get_x() + b.get_width() / 2, h),
                                textcoords="offset points", xytext=(0, 4),
                                ha="center", fontsize=9, color="#333333")

            ax.set_title(spec.get("title", f"Chart {i+1}"), fontsize=13, fontweight="bold",
                         color="#1A1A2E", pad=14)
            ax.set_ylabel(spec.get("y_label", ""))
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", color="#EAEAF2", linewidth=0.8, zorder=0)
            ax.set_axisbelow(True)
            plt.xticks(rotation=25, ha="right")
            plt.tight_layout()
            path = os.path.join(output_dir, f"chart_{i+1}.png")
            fig.savefig(path, facecolor="white")
            plt.close(fig)
            paths.append(path)
        except Exception:
            continue
    return paths


def generate_image_queries(query: str, subquestions: list[str], max_queries: int = 3) -> list[str]:
    """
    Sub-questions are full sentences ("What is the current adoption rate of...") which
    make terrible stock-photo search terms. This asks Gemini to distill the topic into
    short, concrete, visual phrases instead — the kind of thing you'd actually type into
    a photo search bar.
    """
    prompt = (
        f"Research topic: \"{query}\"\n"
        f"Sub-questions covered: {'; '.join(subquestions)}\n\n"
        f"Generate {max_queries} short stock-photo search phrases (2-5 words each) that "
        f"would find CONCRETE, VISUALLY SPECIFIC images related to this topic — real "
        f"objects, equipment, people, places, or scenes from this domain. Avoid abstract "
        f"or generic corporate phrases like 'business technology' or 'digital innovation'. "
        f"Prefer tangible nouns (e.g. for 'quantum computing', prefer 'quantum computer chip' "
        f"over 'future technology')."
    )
    schema = '["short visual phrase 1", "short visual phrase 2", "short visual phrase 3"]'
    try:
        phrases = generate_json(prompt, schema)
    except Exception:
        phrases = []
    phrases = [str(p) for p in phrases] if isinstance(phrases, list) else []
    return phrases[:max_queries] if phrases else [query]


def find_supporting_images(query: str, subquestions: list[str], output_dir: str,
                            max_images: int = 3) -> list[str]:
    """
    Finds relevant stock photos and downloads them locally so they can be embedded
    in the PDF/DOCX (not just linked externally). Returns local file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    search_phrases = generate_image_queries(query, subquestions, max_images)

    urls = []
    for phrase in search_phrases:
        url = find_image(phrase)
        if url:
            urls.append(url)
    if not urls:
        url = find_image(query)
        if url:
            urls.append(url)

    paths = []
    for i, url in enumerate(urls):
        dest = os.path.join(output_dir, f"image_{i+1}.jpg")
        if download_image(url, dest):
            paths.append(dest)
    return paths
