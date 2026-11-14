"""Draws the pipeline diagram used in the report and slides."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

def box(ax, x, y, w, h, title, body, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color, ec="#1f2d3d", lw=1.4))
    ax.text(x + w/2, y + h - 0.16, title, ha="center", va="top", fontsize=10.5, weight="bold", color="#1f2d3d")
    ax.text(x + w/2, y + h/2 - 0.12, body, ha="center", va="center", fontsize=8.6, color="#1f2d3d", linespacing=1.35)

def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#1f2d3d"))

fig, ax = plt.subplots(figsize=(11, 4.6), dpi=200)
ax.set_xlim(0, 11); ax.set_ylim(0, 4.6); ax.axis("off")

# offline (indexing) row
box(ax, 0.2, 2.75, 2.2, 1.55, "1. NED rule PDFs", "Admission & Studies\nRegulations (2025)\nExamination\nRegulations (2024)", "#e8eef7")
box(ax, 2.9, 2.75, 2.2, 1.55, "2. Clause chunking", "split by clause number\n(e.g. ADM 7.5, page 5)\n174 chunks + metadata", "#e8eef7")
box(ax, 5.6, 2.75, 2.4, 1.55, "3. Indexes", "BM25 (keywords)\nchar n-gram TF-IDF\nmultilingual embeddings", "#e8eef7")
arrow(ax, 2.4, 3.5, 2.9, 3.5); arrow(ax, 5.1, 3.5, 5.6, 3.5)
ax.text(0.2, 4.45, "Indexing (done once)", fontsize=10, weight="bold", color="#51627a")

# online (question) row
box(ax, 0.2, 0.25, 2.2, 1.75, "A. Student question", "English or Roman Urdu\n\"Exam ke liye kitni\nhazri chahiye?\"", "#fdf1e3")
box(ax, 2.9, 0.25, 2.2, 1.75, "B. Normalisation", "Roman Urdu lexicon\nhazri -> attendance\nfiller words removed", "#fdf1e3")
box(ax, 5.6, 0.25, 2.4, 1.75, "C. Retrieval", "BM25 / dense / hybrid\n(reciprocal rank fusion)\ntop-k clauses", "#fdf1e3")
box(ax, 8.5, 0.25, 2.3, 1.75, "D. Grounded answer", "LLM answers only from\nretrieved clauses, cites\n[EXM 3.5], or refuses", "#e5f4ea")
arrow(ax, 2.4, 1.1, 2.9, 1.1); arrow(ax, 5.1, 1.1, 5.6, 1.1); arrow(ax, 8.0, 1.1, 8.5, 1.1)
arrow(ax, 6.8, 2.75, 6.8, 2.0)
ax.text(0.2, 2.2, "Answering (every question)", fontsize=10, weight="bold", color="#51627a")
box(ax, 8.5, 2.75, 2.3, 1.55, "Evaluation", "Recall@k, MRR\ncorrectness, faithfulness\ncitation & refusal rate", "#f3e8f7")
arrow(ax, 9.65, 2.0, 9.65, 2.75)
plt.tight_layout()
plt.savefig("pipeline.png", bbox_inches="tight", facecolor="white")
print("saved pipeline.png")
