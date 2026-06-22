"""
Color palette and theming for the warehouse visualization.

Redesigned light theme designed for a modern operations monitoring dashboard,
directly styled using the clean off-white, slate text, and warm terracotta-orange
color language from the reference dashboard.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BASE THEME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BG_PRIMARY = (244, 246, 248)          # Main light background
BG_SECONDARY = (255, 255, 255)        # Panels background (pure white)
BG_TERTIARY = (255, 255, 255)         # Card backgrounds (pure white)
BG_CONTROL = (255, 255, 255)          # Control panel background

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GRID CELL COLORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CELL_AISLE_COLOR = (255, 255, 255)        # Walkable aisles (clean white floor)
CELL_SHELF_COLOR = (241, 242, 244)        # Storage racks (soft grey)
CELL_SHELF_BORDER = (226, 228, 232)       # Shelf border for subtle 3D separation
CELL_PACKING_COLOR = (39, 174, 96)         # Packing station — green
CELL_DISPATCH_COLOR = (41, 128, 185)       # Dispatch area — blue
GRID_LINE_COLOR = (234, 234, 236)         # Faint grid lines

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SKU / ITEM COLORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITEM_DEFAULT = (116, 122, 128)            # Standard item on shelf (muted grey)
ITEM_IN_ORDER = (241, 196, 15)             # Highlighted — in current order (yellow border)
ITEM_CLASS_A = (222, 92, 60)              # High demand — terracotta orange
ITEM_CLASS_B = (229, 146, 116)            # Medium demand — saturated peach orange
ITEM_CLASS_C = (236, 190, 175)            # Low demand — solid pink-peach

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PATH & ROUTE COLORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATH_COLOR = (222, 92, 60)                # BFS path overlay — terracotta orange
ROUTE_LINE_COLOR = (26, 29, 32)           # Optimized route line — solid charcoal
ROUTE_LINE_NN = (116, 122, 128)           # NN route line — muted grey

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PICKER COLORS (simultaneous pickers)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKER_COLORS = [
    (155, 89, 182),     # Purple
    (230, 126, 34),     # Orange
    (26, 188, 156),     # Teal
    (52, 152, 219),     # Blue
    (241, 196, 15),     # Yellow
    (231, 76, 60),      # Red
    (46, 204, 113),     # Green
    (255, 105, 180),    # Hot Pink
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEXT HIERARCHY (Light theme)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEXT_PRIMARY = (26, 29, 32)               # Slate text
TEXT_SECONDARY = (116, 122, 128)          # Muted grey / sub-labels
TEXT_ACCENT = (222, 92, 60)               # Accent — terracotta orange
TEXT_HEADER = (17, 17, 17)                # Deep black headers

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UI ELEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUTTON_NORMAL = (241, 242, 244)           # Light grey
BUTTON_HOVER = (226, 228, 232)            # Soft hover grey
BUTTON_ACTIVE = (222, 92, 60)             # Terracotta active
BUTTON_TEXT = (26, 29, 32)                # Dark text

SLIDER_TRACK = (226, 228, 232)            # Light track
SLIDER_FILL = (222, 92, 60)               # Terracotta fill
SLIDER_HANDLE = (26, 29, 32)              # Charcoal grabber

DIVIDER = (226, 228, 232)                 # Light grey dividers

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STATUS INDICATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS_SUCCESS = (39, 174, 96)            # Green
STATUS_WARNING = (241, 196, 15)            # Yellow
STATUS_DANGER = (222, 92, 60)             # Terracotta
STATUS_INFO = (47, 128, 237)              # Blue

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEATMAP GRADIENT (cold → hot)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEATMAP_GRADIENT = [
    (253, 229, 216),    # Low Demand: #FDE5D8
    (250, 198, 169),    # Low-Medium Transition
    (248, 168, 122),    # Medium Demand: #F8A87A
    (240, 130, 82),     # Medium-High Transition
    (232, 93, 42),      # High Demand: #E85D2A
]
