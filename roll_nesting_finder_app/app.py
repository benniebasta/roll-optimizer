import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import itertools
import random

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="AD ON RIP Optimizer", page_icon="🖨", layout="wide")

# ===============================
# CUSTOM STYLE
# ===============================
st.markdown("""
<style>
/* Main header banner */
.adon-header {
    background: linear-gradient(135deg, #1a2a6c 0%, #2a4d9b 50%, #00b4d8 100%);
    padding: 1.6rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.2rem;
}
.adon-header h1 {
    color: white;
    margin: 0;
    font-size: 2rem;
}
.adon-header p {
    color: #cfe8ff;
    margin: 0.3rem 0 0 0;
    font-size: 1rem;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: #f6f9ff;
    border: 1px solid #dce6f5;
    border-radius: 14px;
    padding: 14px 18px;
    box-shadow: 0 2px 6px rgba(26, 42, 108, 0.07);
}
div[data-testid="stMetricValue"] {
    color: #1a2a6c;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1a2a6c, #00b4d8);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.6rem;
    font-weight: 600;
    transition: 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0, 180, 216, 0.45);
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #f4f7fc;
}

/* Dataframe corners */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# HEADER
# ===============================
st.markdown("""
<div class="adon-header">
    <h1>🖨 AD ON Roll Optimizer + RIP Nesting</h1>
    <p>AD ON Exhibition / Display GURU</p>
</div>
""", unsafe_allow_html=True)

# ===============================
# AVAILABLE ROLL WIDTHS
# ===============================
ROLL_WIDTHS = [
    50, 51, 91, 94, 100, 105, 106, 110, 112, 120,
    127, 137, 152, 160, 162, 200, 240, 250,
    257, 260, 310, 320
]

# Fixed pleasant colors for the layout drawing
PALETTE = plt.cm.tab20.colors

# ===============================
# MAIN NAVIGATION
# ===============================
st.sidebar.markdown("## 📂 Navigation")
page = st.sidebar.radio(
    "Choose a tool",
    ["📏 Roll Finder", "🖨 RIP Optimizer"],
    label_visibility="collapsed"
)
st.sidebar.divider()

# ============================================================
# PAGE 1 : MATERIAL WIDTH FINDER
# ============================================================
if page == "📏 Roll Finder":
    st.subheader("📏 Material Width Optimizer")
    st.caption("Enter your artwork size to find the roll width with the least waste.")

    c1, c2 = st.columns(2)
    with c1:
        w = st.number_input("Artwork Width (cm)", min_value=1.0)
    with c2:
        h = st.number_input("Artwork Height (cm)", min_value=1.0)

    def find_top10(art_w, art_h):
        results = []
        for roll in ROLL_WIDTHS:

            # Normal orientation
            if art_w <= roll:
                used = roll * art_h
                real = art_w * art_h
                waste = used - real
                results.append((roll, "Normal", art_h, waste))

            # Rotated 90°
            if art_h <= roll:
                used = roll * art_w
                real = art_w * art_h
                waste = used - real
                results.append((roll, "Rotated 90°", art_w, waste))

        results.sort(key=lambda x: (x[3], x[0]))
        return results[:10]

    if st.button("🔍 Find Best Roll Width"):
        top10 = find_top10(w, h)

        if not top10:
            st.error("❌ This artwork does not fit any roll.")
        else:
            best_roll, best_orient, best_len, best_waste = top10[0]

            m1, m2, m3 = st.columns(3)
            m1.metric("🏆 Best Roll", f"{best_roll} cm")
            m2.metric("Orientation", best_orient)
            m3.metric("Waste", f"{best_waste/10000:.2f} m²")

            df = pd.DataFrame(top10, columns=[
                "Roll Width (cm)",
                "Orientation",
                "Used Length (cm)",
                "Waste Area (cm²)"
            ])
            df.index = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True)

            st.info("👉 Pick the best Roll Width and use it in the RIP Optimizer page.")

# ============================================================
# PAGE 2 : RIP NESTING OPTIMIZER
# ============================================================
else:

    st.subheader("🖨 RIP-Grade Guillotine Optimizer")
    st.caption("Set your roll and panels in the sidebar, then run the optimizer.")

    st.sidebar.markdown("## ⚙️ Settings")
    ROLL_WIDTH = st.sidebar.number_input("Roll Width (cm)", value=137.0)
    OVERLAP = st.sidebar.number_input("Tile Overlap (cm)", value=1.0)
    ITERATIONS = st.sidebar.number_input("Optimization Passes", 20, 500, 150)

    AUTO_ROTATE = st.sidebar.toggle("🔄 Auto Rotate", value=False)
    if AUTO_ROTATE:
        st.sidebar.caption("ON → tries rotating panels 90° to use the least material.")
    else:
        st.sidebar.caption("OFF → panels keep their given orientation.")

    st.sidebar.divider()
    st.sidebar.markdown("## 🧩 Panels")
    panel_count = st.sidebar.number_input("Number of different panels", 1, 50, 5)

    jobs = []
    for i in range(1, panel_count + 1):
        with st.sidebar.expander(f"Panel {i}", expanded=(i == 1)):
            w = st.number_input(f"Width (cm)", 0.0, key=f"w{i}")
            h = st.number_input(f"Height (cm)", 0.0, key=f"h{i}")
            q = st.number_input(f"Quantity", min_value=0.0, max_value=None, value=0.0, step=1.0, key=f"q{i}")
            if w > 0 and h > 0 and q > 0:
                jobs.append((i, w, h, int(round(q))))
                st.caption(f"✅ {int(round(q))} × {w:g}×{h:g} cm")

    # =========================================
    # TILING
    # =========================================
    def tile_width_only(w, roll):
        for n in [1, 2, 3, 4, 5]:
            if w <= n * roll - (n - 1) * OVERLAP:
                return (w + (n - 1) * OVERLAP) / n, n
        return None, None

    # =========================================
    # GUILLOTINE PACKER  (UNCHANGED)
    # =========================================
    def pack(pieces):
        free = [(0, 0, ROLL_WIDTH, 10000)]
        placed = []

        for p in pieces:
            best = None
            for fx, fy, fw, fh in free:
                for w, h in p["orientations"]:
                    if w <= fw and h <= fh:
                        waste = fw * fh - w * h
                        if not best or waste < best[0]:
                            best = (waste, fx, fy, fw, fh, w, h)

            if not best:
                return None

            _, fx, fy, fw, fh, w, h = best
            placed.append((p["pid"], fx, fy, w, h))
            free.remove((fx, fy, fw, fh))

            right = (fx + w, fy, fw - w, h)
            bottom = (fx, fy + h, fw, fh - h)

            if right[2] > 0 and right[3] > 0:
                free.append(right)
            if bottom[2] > 0 and bottom[3] > 0:
                free.append(bottom)

        return placed

    def length(placed):
        if not placed:
            return 0
        return max(y + h for _, _, y, _, h in placed)

    # =========================================
    # OFF PATH  (NO ROTATION)
    # =========================================
    def expand(jobs):
        pieces = []
        for pid, w, h, q in jobs:
            tile_w, n = tile_width_only(w, ROLL_WIDTH)
            if tile_w is None:
                return None
            for _ in range(q):
                for _ in range(n):
                    pieces.append({
                        "pid": pid,
                        "orientations": [(tile_w, h)]
                    })
        return pieces

    def optimize(pieces):
        best_len = None
        best_layout = None

        for _ in range(ITERATIONS):
            random.shuffle(pieces)
            layout = pack(pieces)
            if layout:
                l = length(layout)
                if not best_len or l < best_len:
                    best_len = l
                    best_layout = layout

        return best_layout, best_len

    # =========================================
    # ON PATH  (AUTO ROTATE)
    # =========================================
    def build_groups(jobs):
        groups = []
        for pid, w, h, q in jobs:
            tile_w, n = tile_width_only(w, ROLL_WIDTH)
            if tile_w is None:
                return None

            orients = [(tile_w, h)]
            if h <= ROLL_WIDTH and abs(h - tile_w) > 1e-9:
                orients.append((h, tile_w))

            groups.append({"pid": pid, "orients": orients, "count": q * n})
        return groups

    def optimize_rotate(groups):
        option_lists = [g["orients"] for g in groups]
        all_combos = list(itertools.product(*option_lists))

        seeds = [
            tuple(opts[0] for opts in option_lists),
            tuple(opts[-1] for opts in option_lists),
        ]
        if len(all_combos) > ITERATIONS:
            sampled = random.sample(all_combos, int(ITERATIONS))
            combos = list({*seeds, *sampled})
        else:
            combos = all_combos

        passes = max(1, int(ITERATIONS) // max(1, len(combos)))

        best_len = None
        best_layout = None

        for combo in combos:
            base = []
            for g, (w, h) in zip(groups, combo):
                for _ in range(g["count"]):
                    base.append({"pid": g["pid"], "orientations": [(w, h)]})

            for _ in range(passes):
                random.shuffle(base)
                layout = pack(base)
                if layout:
                    l = length(layout)
                    if best_len is None or l < best_len:
                        best_len = l
                        best_layout = layout

        return best_layout, best_len

    # =========================================
    # RUN
    # =========================================
    if st.button("🚀 Run RIP Optimizer"):
        if not jobs:
            st.error("❌ Add at least one panel with width, height and quantity.")
            st.stop()

        with st.spinner("Optimizing layout…"):
            if AUTO_ROTATE:
                groups = build_groups(jobs)
                if groups is None:
                    st.error("❌ Some panels cannot fit the roll width.")
                    st.stop()
                best, total = optimize_rotate(groups)
            else:
                pieces = expand(jobs)
                if not pieces:
                    st.error("❌ Some panels cannot fit the roll width.")
                    st.stop()
                best, total = optimize(pieces)

        if not best:
            st.error("❌ Could not produce a layout.")
            st.stop()

        # ===== Result metrics =====
        used_area = sum(w * h for _, _, _, w, h in best)
        roll_area = ROLL_WIDTH * total
        utilization = used_area / roll_area * 100 if roll_area else 0
        mode = "Auto Rotate ON" if AUTO_ROTATE else "Auto Rotate OFF"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📏 Fabric Length", f"{total/100:.2f} m")
        m2.metric("🧩 Pieces Placed", f"{len(best)}")
        m3.metric("📊 Material Used", f"{utilization:.1f} %")
        m4.metric("🔄 Mode", mode.replace("Auto Rotate ", ""))

        # ===== Layout drawing =====
        st.markdown("#### 🗺 Nesting Layout")
        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor("#f6f9ff")
        ax.set_facecolor("white")
        colors = {}

        for pid, x, y, w, h in best:
            if pid not in colors:
                colors[pid] = PALETTE[(pid - 1) % len(PALETTE)]
            ax.add_patch(plt.Rectangle(
                (y, x), h, w,
                facecolor=colors[pid],
                edgecolor="#1a2a6c",
                linewidth=1.2,
                alpha=0.9
            ))
            ax.text(
                y + h / 2,
                x + w / 2,
                f"P{pid}\n{w:.0f}×{h:.0f}",
                ha="center",
                va="center",
                fontsize=8,
                weight="bold",
                color="#1a2a6c"
            )

        ax.set_xlim(0, total)
        ax.set_ylim(0, ROLL_WIDTH)
        ax.set_xlabel("Fabric Length (cm)", fontsize=11, color="#1a2a6c")
        ax.set_ylabel("Roll Width (cm)", fontsize=11, color="#1a2a6c")
        ax.set_title(f"RIP-Grade Guillotine Nesting — Roll {ROLL_WIDTH:g} cm",
                     fontsize=13, weight="bold", color="#1a2a6c")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)

        st.pyplot(fig)

        # ===== Cut list =====
        st.markdown("#### 📋 Cut List")
        df = pd.DataFrame([(f"P{p}", w, h) for p, _, _, w, h in best],
                          columns=["Panel", "Tile Width (cm)", "Tile Height (cm)"])
        summary = df.groupby(["Panel", "Tile Width (cm)", "Tile Height (cm)"]) \
                    .size().reset_index(name="Count")
        st.dataframe(summary, use_container_width=True)
