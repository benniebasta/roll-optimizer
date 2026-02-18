import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="AD ON RIP Optimizer", layout="wide")
st.title("🖨 AD ON Roll Optimizer + RIP Nesting")
st.caption("AD ON Exhibition / Display GURU")

# ===============================
# AVAILABLE ROLL WIDTHS
# ===============================
ROLL_WIDTHS = [
    50, 51, 91, 94, 100, 105, 106, 110, 112, 120,
    127, 137, 152, 160, 162, 200, 240, 250,
    257, 260, 310, 320
]

# ===============================
# APP TABS
# ===============================
tab1, tab2 = st.tabs(["📏 Roll Finder", "🖨 RIP Optimizer"])

# ============================================================
# TAB 1 : MATERIAL WIDTH FINDER
# ============================================================
with tab1:
    st.header("📏 Material Width Optimizer")

    w = st.number_input("Artwork Width (cm)", min_value=1.0)
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

    if st.button("Find Best Roll Width"):
        top10 = find_top10(w, h)

        if not top10:
            st.error("❌ This artwork does not fit any roll.")
        else:
            df = pd.DataFrame(top10, columns=[
                "Roll Width (cm)",
                "Orientation",
                "Used Length (cm)",
                "Waste Area (cm²)"
            ])
            st.dataframe(df, use_container_width=True)

            st.info("👉 Pick the best Roll Width and use it in the RIP Optimizer tab.")

# ============================================================
# TAB 2 : RIP NESTING OPTIMIZER
# ============================================================
with tab2:

    st.header("🖨 RIP-Grade Guillotine Optimizer")

    ROLL_WIDTH = st.sidebar.number_input("Roll Width (cm)", value=137.0)
    OVERLAP = st.sidebar.number_input("Tile Overlap (cm)", value=1.0)
    ITERATIONS = st.sidebar.number_input("Optimization Passes", 20, 500, 150)

    st.sidebar.header("Panels")
    panel_count = st.sidebar.number_input("Number of different panels", 1, 50, 5)

    jobs = []
    for i in range(1, panel_count + 1):
        st.sidebar.markdown(f"### Panel {i}")
        w = st.sidebar.number_input(f"W{i} (cm)", 0.0, key=f"w{i}")
        h = st.sidebar.number_input(f"H{i} (cm)", 0.0, key=f"h{i}")
        q = st.sidebar.number_input(f"Qty{i}", 0, 200, 0, key=f"q{i}")
        if w > 0 and h > 0 and q > 0:
            jobs.append((i, w, h, q))

    # =========================================
    # TILING
    # =========================================
    def tile_width_only(w, roll):
        for n in [1, 2, 3, 4, 5]:
            if w <= n * roll - (n - 1) * OVERLAP:
                return (w + (n - 1) * OVERLAP) / n, n
        return None, None

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
                        "orientations": [(tile_w, h), (h, tile_w)]
                    })
        return pieces

    # =========================================
    # GUILLOTINE PACKER
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
        return max(y + h for _, _, y, _, h in placed)

    # =========================================
    # ANNEALING MULTI-PASS
    # =========================================
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
    # RUN
    # =========================================
    if st.button("Run RIP Optimizer"):
        pieces = expand(jobs)
        if not pieces:
            st.error("❌ Some panels cannot fit the roll width.")
            st.stop()

        best, total = optimize(pieces)

        st.success(f"✅ RIP-Optimized Fabric Length = {total/100:.2f} meters")

        df = pd.DataFrame([(p,w,h) for p,_,_,w,h in best],
                          columns=["Panel","Tile Width","Tile Height"])
        st.dataframe(df, use_container_width=True)

        # ===== Visualization =====
        fig, ax = plt.subplots(figsize=(14,8))
        colors = {}

        for pid, x, y, w, h in best:
            if pid not in colors:
                colors[pid] = (random.random(), random.random(), random.random())
            ax.add_patch(plt.Rectangle((y, x), h, w, facecolor=colors[pid], edgecolor="black"))
            ax.text(
                y + h/2,
                x + w/2,
                f"{pid}\n{w:.0f}×{h:.0f}",
                ha="center",
                va="center",
                fontsize=8,
                weight="bold"
            )

        ax.set_xlim(0, total)
        ax.set_ylim(0, ROLL_WIDTH)
        ax.set_xlabel("Fabric Length (cm)")
        ax.set_ylabel("Roll Width (cm)")
        ax.set_title("RIP-Grade Guillotine Nesting")

        st.pyplot(fig)
