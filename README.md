# Quick-Commerce Dark Store Operations Simulator

A highly realistic, agent-based software model simulating the operations of a Quick-Commerce Dark Store (e.g., Blinkit, Zepto, Instamart). This academic project focuses on operations research, demonstrating advanced algorithms for warehouse storage optimization, order picking, and dynamic demand forecasting.

## 🚀 Features

### 1. Operations Research Algorithms
- **Exact Bitmask DP TSP Routing**: Computes the mathematically optimal routing path for pickers fulfilling customer orders (for orders ≤ 12 items).
- **Nearest Neighbor Fallback**: An efficient heuristic for massive B2B-style bulk orders.
- **Greedy Slotting Optimization**: Continuously analyzes SKU demand velocity to physically relocate high-demand items closer to the packing station.
- **ABC Classification**: Automatically groups inventory into Class A (high demand), B (medium demand), and C (low demand).
- **Exponential Smoothing Forecasts**: Predicts future SKU demand based on temporal history and Time-of-Day shifting.

### 2. Realistic Warehouse Environment
- **Massive Multi-location Catalog**: Over 50+ unique groceries and household items. High-velocity items occupy multiple physical shelf locations dynamically.
- **Multi-Agent Picker Fleet**: Simulates 8 concurrent human pickers dynamically accepting orders and pathfinding across the aisles without collision deadlocks.
- **Live Event Loop**: Capable of generating hundreds of random customer orders and routing them continuously in a high-density environment.

### 3. Advanced Pygame Visualization
- **Interactive Operations Dashboard**: Custom widescreen UI featuring live queue tracking, picker utilization metrics, and warehouse density statistics.
- **Custom Cart Builder**: Click on items in the live product catalog to build custom user orders and inject them directly into the pathfinding queue.
- **Visual Analytics**: Real-time traffic heatmaps, picker routing comet-trails, and interactive mouse-hover product tooltips.
- **Re-slotting Animations**: When the layout is optimized, relocated items physically flash on the screen accompanied by an ROI notification banner.

## ⚙️ Architecture

The project adheres to a clean, highly modular architecture to support future algorithmic expansions:

- `project/algorithms/`: Routing, Slotting, Pathfinding, and Forecasting logic.
- `project/simulation/`: The live event loop entities (Pickers, Orders, Heatmaps, Congestion tracking).
- `project/warehouse/`: The physical bounds, layout generation, and core Inventory Catalog definitions.
- `project/visualization/`: Pygame rendering engine, UI state tracking, and color palettes.
- `project/experiments/`: Headless scripts for executing scalability tests and mathematical strategy comparisons.

## 🖥️ Usage

### Run the Live Interactive UI (Pygame)
```bash
python run.py
```
- Press **`[SPACE]`** to generate random orders instantly.
- Press **`[D]`** to toggle automated Presentation Demo mode.
- Press **`[T]`** to cycle the Time of Day (Morning/Afternoon/Evening) and shift demand priorities.
- Press **`[O]`** to force a physical warehouse Re-slotting optimization.
- Press **`[H]`** to toggle the traffic heatmap overlay.

### Run Strategy Benchmarks (Headless)
Execute 1,000 algorithmic order simulations to empirically prove the distance savings of Greedy vs Random placement:
```bash
python run.py --experiment
```
