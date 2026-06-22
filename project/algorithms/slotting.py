"""
Advanced Slotting Engine supporting multiple strategies and cost modeling.
"""
from typing import Any
import random
from project.warehouse.layout import WarehouseLayout
from project.warehouse.inventory import InventoryManager, SKUInfo
from project.algorithms.pathfinding import bfs_shortest_path
from project.algorithms.forecasting import DemandForecaster
from project.config import W_DEMAND, W_ABC, W_DISTANCE, LABOR_COST_PER_MOVE, MOVEMENT_COST_PER_UNIT, DISRUPTION_COST_PER_MOVE

class SlottingEngine:
    def __init__(self):
        self.abc_priorities = {"A": 3, "B": 2, "C": 1}
        self.total_reslot_cost = 0.0
        self.last_reslot_cost = 0.0

    def _calculate_greedy_score(self, sku: SKUInfo) -> float:
        abc_pri = self.abc_priorities.get(sku.abc_class, 1)
        return W_DEMAND * sku.velocity + W_ABC * abc_pri + W_DISTANCE * 1.0

    def _calculate_forecast_score(self, sku: SKUInfo, forecaster: DemandForecaster) -> float:
        abc_pri = self.abc_priorities.get(sku.abc_class, 1)
        forecast_demand = forecaster.forecasts.get(sku.sku_id, sku.velocity)
        return W_DEMAND * forecast_demand + W_ABC * abc_pri + W_DISTANCE * 1.0

    def optimize_slotting(self, inventory: InventoryManager, layout: WarehouseLayout, strategy: str = "Greedy", forecaster: DemandForecaster = None, force: bool = False) -> dict[str, Any]:
        """
        Assigns SKUs to shelves based on the selected strategy.
        Supports: Random, ABC, Greedy, ForecastDriven.
        Calculates Net Benefit = Distance Savings - Re-slot Cost.
        """
        skus = inventory.get_all_skus()
        shelves = layout.get_shelf_cells()
        
        if not skus or not shelves:
            return {"strategy": strategy, "items_moved": 0, "net_benefit": 0.0}
 
        packing = layout.packing_station
        
        # 1. Sort shelves by ascending BFS distance from packing station
        shelf_distances = []
        for shelf in shelves:
            aisle = layout.get_adjacent_aisle(shelf)
            if aisle:
                _, dist = bfs_shortest_path(layout, packing, aisle)
                shelf_distances.append((shelf, dist))
            else:
                shelf_distances.append((shelf, float('inf')))
                
        shelves_sorted = sorted(shelf_distances, key=lambda x: x[1])
 
        # 2. Rank SKUs based on strategy
        if strategy == "Random":
            skus_sorted = list(skus)
            random.shuffle(skus_sorted)
        elif strategy == "ABC":
            skus_sorted = sorted(skus, key=lambda s: self.abc_priorities.get(s.abc_class, 1), reverse=True)
        elif strategy == "ForecastDriven" and forecaster:
            skus_sorted = sorted(skus, key=lambda s: self._calculate_forecast_score(s, forecaster), reverse=True)
        else: # Default Greedy
            skus_sorted = sorted(skus, key=lambda s: self._calculate_greedy_score(s), reverse=True)
        
        # 3. Compute cost and distance
        items_moved = 0
        total_old_dist = 0.0
        total_new_dist = 0.0
        move_cost = 0.0
        
        old_mapping = {sku.sku_id: sku.location for sku in skus}
        new_mapping = {}
        
        for i, sku in enumerate(skus_sorted):
            if i < len(shelves_sorted):
                new_shelf, new_dist = shelves_sorted[i]
                new_mapping[sku.sku_id] = new_shelf
                old_shelf = old_mapping[sku.sku_id]
                
                if old_shelf:
                    old_aisle = layout.get_adjacent_aisle(old_shelf)
                    if old_aisle:
                        _, old_dist = bfs_shortest_path(layout, packing, old_aisle)
                        total_old_dist += old_dist
                else:
                    total_old_dist += new_dist
                    
                total_new_dist += new_dist
                
                if old_shelf != new_shelf:
                    items_moved += 1
                    move_cost += (LABOR_COST_PER_MOVE + MOVEMENT_COST_PER_UNIT + DISRUPTION_COST_PER_MOVE)
 
        # 4. Evaluate Benefit
        distance_savings = total_old_dist - total_new_dist
        net_benefit = distance_savings - move_cost
        
        moved_skus = []
        if net_benefit > 0 or items_moved == len(skus) or force:
            for sku_id, new_shelf in new_mapping.items():
                if old_mapping[sku_id] != new_shelf:
                    moved_skus.append(sku_id)
                inventory.assign_location(sku_id, new_shelf)
            self.last_reslot_cost = move_cost
            self.total_reslot_cost += move_cost
            executed = True
        else:
            executed = False
            items_moved = 0
            distance_savings = 0.0

        return {
            "strategy": strategy,
            "items_moved": items_moved,
            "distance_savings": distance_savings,
            "move_cost": move_cost,
            "net_benefit": net_benefit,
            "executed": executed,
            "avg_storage_distance": total_new_dist / len(skus_sorted) if executed else total_old_dist / len(skus_sorted),
            "old_dist_total": total_old_dist,
            "new_dist_total": total_new_dist,
            "moved_skus": moved_skus
        }
