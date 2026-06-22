"""
Main entry point for Realistic Dark Store Simulator.
"""
import sys
import random
import argparse
import pygame
import pygame.gfxdraw
import time
from project.warehouse.layout import WarehouseLayout
from project.warehouse.inventory import InventoryManager
from project.algorithms.slotting import SlottingEngine
from project.algorithms.forecasting import DemandForecaster
from project.algorithms.pathfinding import bfs_shortest_path, compute_bfs_distance_matrix
from project.algorithms.routing import plan_route
from project.simulation.picker import Picker, PickerState
from project.simulation.congestion import CongestionManager
from project.simulation.heatmap import HeatmapManager
from project.simulation.orders import OrderManager, Order
from project.algorithms.assignment import assign_nearest_available_picker
from project.visualization.renderer import Renderer
from project.visualization.colors import PICKER_COLORS, TEXT_PRIMARY, SLIDER_TRACK, SLIDER_FILL
from project.visualization.ui_state import UIState
from project.config import FPS, PICKER_BASE_SPEED


# --- Lightweight Slider widget (ported from manual_sim for manual-mode control) ---
class Slider:
    def __init__(self, x, y, w, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.handle_radius = 8
        self.update_handle_pos()
        self.dragging = False

    def update_handle_pos(self):
        fraction = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_x = self.rect.x + int(fraction * self.rect.width)

    def set_rect(self, x, y, w):
        self.rect.x = x
        self.rect.y = y
        self.rect.width = w
        self.update_handle_pos()

    def draw(self, surface, font_obj):
        lbl = font_obj.render(f"{self.label}: {int(self.val) if self.val == int(self.val) else round(self.val,1)}", True, TEXT_PRIMARY)
        surface.blit(lbl, (self.rect.x, self.rect.y - 18))
        # Draw thin background track
        track_rect = pygame.Rect(self.rect.x, self.rect.y + 3, self.rect.width, 4)
        pygame.draw.rect(surface, SLIDER_TRACK, track_rect, border_radius=2)
        # Draw filled track (left of handle)
        filled_width = self.handle_x - self.rect.x
        if filled_width > 0:
            filled_rect = pygame.Rect(self.rect.x, self.rect.y + 3, filled_width, 4)
            pygame.draw.rect(surface, SLIDER_FILL, filled_rect, border_radius=2)
        # Draw handle
        pygame.gfxdraw.aacircle(surface, self.handle_x, self.rect.y + 5, self.handle_radius, SLIDER_FILL)
        pygame.gfxdraw.filled_circle(surface, self.handle_x, self.rect.y + 5, self.handle_radius, SLIDER_FILL)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if ((mouse_pos[0] - self.handle_x) ** 2 + (mouse_pos[1] - (self.rect.y + 5)) ** 2) ** 0.5 <= self.handle_radius + 4:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mx = max(self.rect.x, min(event.pos[0], self.rect.x + self.rect.width))
            fraction = (mx - self.rect.x) / self.rect.width
            self.val = self.min_val + fraction * (self.max_val - self.min_val)
            self.handle_x = mx
            return True
        return False

def route_order(layout: WarehouseLayout, packing_station: tuple[int, int], order_shelves: list[tuple[int, int]]) -> tuple[list[tuple[int, int]], bool, float, int]:
    targets = [packing_station]
    for shelf in order_shelves:
        aisle = layout.get_adjacent_aisle(shelf)
        if aisle:
            targets.append(aisle)
            
    dist_matrix = compute_bfs_distance_matrix(layout, targets)
    route_indices, total_dist, is_dp = plan_route(dist_matrix)
    
    full_path_cells = []
    picking_path_len = 0
    for i in range(len(route_indices) - 1):
        start_idx = route_indices[i]
        end_idx = route_indices[i+1]
        start_cell = targets[start_idx]
        end_cell = targets[end_idx]
        path_segment, _ = bfs_shortest_path(layout, start_cell, end_cell)
        if full_path_cells and path_segment:
            full_path_cells.extend(path_segment[1:])
        else:
            full_path_cells.extend(path_segment)
            
        if i < len(route_indices) - 2:
            picking_path_len = len(full_path_cells)
            
    return full_path_cells, is_dp, total_dist, picking_path_len

def run_ui():
    layout = WarehouseLayout()
    inventory = InventoryManager()
    forecaster = DemandForecaster()
    slotting_engine = SlottingEngine()
    congestion = CongestionManager()
    heatmap = HeatmapManager(layout)
    order_manager = OrderManager(inventory)
    renderer = Renderer()
    ui_state = UIState()
    clock = pygame.time.Clock()

    # --- Manual-mode sliders (position/layout updated each frame) ---
    grid_pixel_width = layout.cols * renderer.tile_size
    right_x = renderer.grid_offset_x + grid_pixel_width + renderer.padding
    slider_width = int(renderer.sidebar_width - 40)
    sx = right_x + 20
    card1_y = renderer.padding
    slider_order_size = Slider(sx, card1_y + 50, slider_width, 2, 11, 4, "Basket Order Size (SKUs)")
    slider_speed = Slider(sx, card1_y + 88, slider_width, 0.5, 4.0, 1.0, "Picker Speed Factor")
    slider_surge_freq = Slider(sx, card1_y + 126, slider_width, 5, 60, 20, "Demand Surge Timer (s)")
    slider_hot_intensity = Slider(sx, card1_y + 164, slider_width, 1, 40, 8, "Surge Intensity")
    sliders = [slider_order_size, slider_speed, slider_surge_freq, slider_hot_intensity]
    last_surge_time = time.time()
    ui_state.sliders = sliders
    
    inventory.generate_inventory()
    shelves = layout.get_shelf_cells()
    random.shuffle(shelves)
    for i, sku in enumerate(inventory.get_all_skus()):
        if i < len(shelves):
            inventory.assign_location(sku.sku_id, shelves[i])
            
    inventory.classify_abc()
    
    strategies = ["ForecastDriven", "Greedy", "ABC", "Random"]
    strategy_idx = 0
    
    metrics = slotting_engine.optimize_slotting(inventory, layout, strategies[strategy_idx], forecaster)
    
    packing_station = layout.packing_station
    pixel_x = renderer.grid_offset_x + packing_station[1] * renderer.tile_size + renderer.tile_size // 2
    pixel_y = renderer.grid_offset_y + packing_station[0] * renderer.tile_size + renderer.tile_size // 2
    
    pickers = [Picker(i+1, packing_station, PICKER_COLORS[i % len(PICKER_COLORS)]) for i in range(8)]
    for p in pickers:
        p.pixel_x, p.pixel_y = pixel_x, pixel_y

    running = True
    demo_mode = False
    tick_counter = 0

    renderer._update_layout(layout, *renderer.screen.get_size())

    while running:
        dt = clock.tick(FPS)
        tick_counter += 1
        ui_state.mouse_pos = pygame.mouse.get_pos()
        renderer._update_layout(layout, *renderer.screen.get_size())
        grid_offset_x = renderer.grid_offset_x
        grid_offset_y = renderer.grid_offset_y
        # Update slider geometry to stick inside right sidebar
        grid_pixel_width = layout.cols * renderer.tile_size
        right_x = renderer.grid_offset_x + grid_pixel_width + renderer.padding
        slider_width = int(renderer.sidebar_width - 40)
        sx = right_x + 20
        
        # Calculate dynamic scaling factor k matching renderer.py
        header_height = 55
        available_height = renderer.screen.get_height() - renderer.padding * 2 - int(header_height * renderer.ui_scale)
        orders_to_show = order_manager.active_orders[:2] + order_manager.pending_orders[:2]
        h_orders_base = 55 if not orders_to_show else (42 + len(orders_to_show[:3]) * 15)
        sum_base = 240 + 115 + 105 + h_orders_base + 80 + 85 + 80
        if available_height > sum_base + 96:
            k = min(1.35, (available_height - 96) / sum_base)
        else:
            k = 1.0
            
        card1_y = renderer.padding + int(header_height * renderer.ui_scale)
        for i, s in enumerate(sliders):
            s.set_rect(sx, card1_y + int(50 * k) + i * int(38 * k), slider_width)
        ui_state.sliders = sliders
        
        # Determine Hovered Cell
        mx, my = ui_state.mouse_pos
        if grid_offset_x <= mx < grid_offset_x + layout.cols * renderer.tile_size and grid_offset_y <= my < grid_offset_y + layout.rows * renderer.tile_size:
            r = (my - grid_offset_y) // renderer.tile_size
            c = (mx - grid_offset_x) // renderer.tile_size
            ui_state.hovered_cell = (r, c)
        else:
            ui_state.hovered_cell = None

        slider_changed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.VIDEORESIZE:
                self_size = (event.w, event.h)
                renderer.screen = pygame.display.set_mode(self_size, pygame.RESIZABLE)
                renderer._update_layout(layout, *self_size)
                continue

            # Feed events to sliders first (manual-mode interactive controls)
            for s in sliders:
                try:
                    if s.handle_event(event):
                        slider_changed = True
                except Exception:
                    pass

            # Mouse clicks and other events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
                if not demo_mode:
                    for sku_id, rect in ui_state.catalog_rects.items():
                        if rect.collidepoint(event.pos):
                            sku = inventory.get_sku(sku_id)
                            if sku: ui_state.add_to_cart(sku)

                    if ui_state.submit_rect and ui_state.submit_rect.collidepoint(event.pos):
                        if ui_state.custom_cart:
                            order_manager.order_counter += 1
                            order = Order(
                                order_id=order_manager.order_counter,
                                customer_id="CUSTOM_UI",
                                items=list(ui_state.custom_cart)
                            )
                            order_manager.pending_orders.append(order)
                            ui_state.clear_cart()

                    if ui_state.clear_rect and ui_state.clear_rect.collidepoint(event.pos):
                        ui_state.clear_cart()

            if event.type == pygame.MOUSEWHEEL:
                if not demo_mode:
                    ui_state.catalog_scroll_y = max(0, min(1000, ui_state.catalog_scroll_y - event.y * 20))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    for _ in range(3):
                        order_manager.generate_customer_order(size=int(slider_order_size.val))
                elif event.key == pygame.K_d:
                    demo_mode = not demo_mode
                elif event.key == pygame.K_t:
                    order_manager.cycle_time_of_day()
                    # Trigger re-slot on time of day change
                    for sku in inventory.get_all_skus():
                        inventory.update_demand(sku.sku_id, random.uniform(0, 10))
                    forecaster.update_forecasts(inventory)
                    inventory.classify_abc()
                    metrics = slotting_engine.optimize_slotting(inventory, layout, strategies[strategy_idx], forecaster)
                    if metrics.get("executed"):
                        ui_state.reslot_timer = 120
                        ui_state.reslot_moved_skus = set(metrics.get("moved_skus", []))
                        old_dist = metrics.get('old_dist_total', 1.0)
                        new_dist = metrics.get('new_dist_total', 1.0)
                        red = max(0.0, (old_dist - new_dist) / old_dist * 100) if old_dist > 0 else 0.0
                        ui_state.reslot_message = f"{metrics.get('items_moved', 0)} items relocated | Est. travel reduction: {red:.1f}%"

                elif event.key == pygame.K_o:
                    for sku in inventory.get_all_skus():
                        inventory.update_demand(sku.sku_id, random.uniform(0, 10))
                    forecaster.update_forecasts(inventory)
                    inventory.classify_abc()
                    metrics = slotting_engine.optimize_slotting(inventory, layout, strategies[strategy_idx], forecaster)
                    if metrics.get("executed"):
                        ui_state.reslot_timer = 120
                        ui_state.reslot_moved_skus = set(metrics.get("moved_skus", []))
                        old_dist = metrics.get('old_dist_total', 1.0)
                        new_dist = metrics.get('new_dist_total', 1.0)
                        red = max(0.0, (old_dist - new_dist) / old_dist * 100) if old_dist > 0 else 0.0
                        ui_state.reslot_message = f"{metrics.get('items_moved', 0)} items relocated | Est. travel reduction: {red:.1f}%"
                        
                elif event.key == pygame.K_s:
                    strategy_idx = (strategy_idx + 1) % len(strategies)
                    metrics = slotting_engine.optimize_slotting(inventory, layout, strategies[strategy_idx], forecaster, force=True)
                    if metrics.get("executed"):
                        ui_state.reslot_timer = 120
                        ui_state.reslot_moved_skus = set(metrics.get("moved_skus", []))
                        old_dist = metrics.get('old_dist_total', 1.0)
                        new_dist = metrics.get('new_dist_total', 1.0)
                        red = max(0.0, (old_dist - new_dist) / old_dist * 100) if old_dist > 0 else 0.0
                        ui_state.reslot_message = f"{metrics.get('items_moved', 0)} items relocated | Est. travel reduction: {red:.1f}%"
                        
                elif event.key == pygame.K_h:
                    renderer.show_heatmap = not renderer.show_heatmap

        if demo_mode:
            if tick_counter % 60 == 0:
                order_manager.generate_customer_order(size=int(slider_order_size.val))
            if tick_counter % 1000 == 0:
                for sku in inventory.get_all_skus():
                    inventory.update_demand(sku.sku_id, random.uniform(0, slider_hot_intensity.val))
                forecaster.update_forecasts(inventory)
                inventory.classify_abc()
                metrics = slotting_engine.optimize_slotting(inventory, layout, strategies[strategy_idx], forecaster)
                if metrics.get("executed"):
                    ui_state.reslot_timer = 120
                    ui_state.reslot_moved_skus = set(metrics.get("moved_skus", []))
                    old_dist = metrics.get('old_dist_total', 1.0)
                    new_dist = metrics.get('new_dist_total', 1.0)
                    red = max(0.0, (old_dist - new_dist) / old_dist * 100) if old_dist > 0 else 0.0
                    ui_state.reslot_message = f"{metrics.get('items_moved', 0)} items relocated | Est. travel reduction: {red:.1f}%"

        # Manual-mode periodic surge driven by sliders
        if not demo_mode:
            if time.time() - last_surge_time > slider_surge_freq.val:
                for _ in range(3):
                    sku = random.choice(inventory.get_all_skus())
                    inventory.update_demand(sku.sku_id, random.uniform(0, slider_hot_intensity.val))
                forecaster.update_forecasts(inventory)
                inventory.classify_abc()
                metrics = slotting_engine.optimize_slotting(inventory, layout, strategies[strategy_idx], forecaster)
                if metrics.get("executed"):
                    ui_state.reslot_timer = 120
                    ui_state.reslot_moved_skus = set(metrics.get("moved_skus", []))
                    old_dist = metrics.get('old_dist_total', 1.0)
                    new_dist = metrics.get('new_dist_total', 1.0)
                    red = max(0.0, (old_dist - new_dist) / old_dist * 100) if old_dist > 0 else 0.0
                    ui_state.reslot_message = f"{metrics.get('items_moved', 0)} items relocated | Est. travel reduction: {red:.1f}%"
                last_surge_time = time.time()

        if ui_state.reslot_timer > 0:
            ui_state.reslot_timer -= 1

        while order_manager.pending_orders:
            picker = assign_nearest_available_picker(pickers, layout, packing_station)
            if picker:
                order = order_manager.get_next_pending_order()
                full_path_cells, _, _, picking_path_len = route_order(layout, packing_station, order.locations)
                picker.assign_route(order, full_path_cells, picking_path_len)
                # Assign precise target pixel logic is handled inside update now, but start pos must be correct
            else:
                break

        for p in pickers:
            # apply manual slider speed multiplier
            p.speed = PICKER_BASE_SPEED * max(0.1, slider_speed.val)
            completed_order = p.update(dt, renderer.tile_size, renderer.padding, grid_offset_x, grid_offset_y)
            if completed_order:
                order_manager.complete_order(completed_order)
            
        congestion.update(pickers, dt)
        heatmap.update(pickers)
                            
        renderer.render(layout, inventory, pickers, metrics, order_manager, congestion, heatmap, forecaster, slotting_engine, demo_mode, ui_state)

    pygame.quit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", action="store_true")
    parser.add_argument("--scalability", action="store_true")
    args = parser.parse_args()
    
    if args.experiment or args.scalability:
        from project.experiments.runner import run_experiment, run_scalability_test
        if args.experiment:
            print("=== STRATEGY COMPARISON ===")
            for s in ["Random", "ABC", "Greedy", "ForecastDriven"]:
                run_experiment(1000, s)
        if args.scalability:
            print("\n=== SCALABILITY ===")
            run_scalability_test()
    else:
        run_ui()

if __name__ == "__main__":
    main()
