"""
Global configuration for the Warehouse Optimization project.

All tunable parameters are centralized here for easy experimentation
and sensitivity analysis. Grid dimensions, slotting weights, algorithm
limits, and display settings are all configurable.

Changing GRID_ROWS/GRID_COLS automatically adjusts the screen resolution.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GRID DIMENSIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRID_ROWS: int = 20
GRID_COLS: int = 25

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CELL TYPE CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CELL_AISLE: int = 0
CELL_SHELF: int = 1
CELL_PACKING: int = 2
CELL_DISPATCH: int = 3

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DISPLAY SETTINGS (auto-adapt to grid size)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TILE_SIZE: int = 32
PADDING: int = 15
LEFT_PANEL_WIDTH: int = 240
SIDEBAR_WIDTH: int = 340
CONTROL_PANEL_HEIGHT: int = 0
FPS: int = 60

# Computed pixel dimensions
GRID_PIXEL_WIDTH: int = GRID_COLS * TILE_SIZE
GRID_PIXEL_HEIGHT: int = GRID_ROWS * TILE_SIZE
SCREEN_WIDTH: int = PADDING + LEFT_PANEL_WIDTH + PADDING + GRID_PIXEL_WIDTH + PADDING + SIDEBAR_WIDTH + PADDING
SCREEN_HEIGHT: int = max(PADDING + GRID_PIXEL_HEIGHT + PADDING + 60, 820)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIMULATION DEFAULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_NUM_SKUS: int = 100
DEFAULT_NUM_PICKERS: int = 1
DEFAULT_SIM_SPEED: float = 1.0
PICKER_BASE_SPEED: float = 4.0      # pixels per frame at speed=1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ABC CLASSIFICATION THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABC_A_PERCENT: float = 0.20          # Top 20% demand → Class A
ABC_B_PERCENT: float = 0.30          # Next 30% → Class B
# Remaining 50% → Class C

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SLOTTING SCORE WEIGHTS (tunable for sensitivity analysis)
#
#  score = w_demand * forecasted_demand
#        + w_abc   * abc_priority
#        + w_distance * (1 / distance_to_packing)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
W_DEMAND: float = 0.6
W_ABC: float = 0.2
W_DISTANCE: float = 0.2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RE-SLOTTING COST PARAMETERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LABOR_COST_PER_MOVE: float = 5.0
MOVEMENT_COST_PER_UNIT: float = 0.5
DISRUPTION_COST_PER_MOVE: float = 2.0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEMAND PROFILES (time-of-day multipliers by category)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEMAND_PROFILES: dict = {
    "morning": {
        "essentials": 1.8, "snacks": 0.6,
        "beverages": 0.8, "general": 1.0,
    },
    "afternoon": {
        "essentials": 1.0, "snacks": 1.2,
        "beverages": 1.0, "general": 1.1,
    },
    "evening": {
        "essentials": 0.7, "snacks": 1.6,
        "beverages": 1.5, "general": 0.9,
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONGESTION PARAMETERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONGESTION_RADIUS: int = 2           # cells
CONGESTION_SPEED_PENALTY: float = 0.5

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ALGORITHM LIMITS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DP_TSP_MAX_ITEMS: int = 12           # Bitmask DP is O(2^n · n²)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FORECASTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORECAST_WINDOW: int = 10
SMOOTHING_ALPHA: float = 0.3
