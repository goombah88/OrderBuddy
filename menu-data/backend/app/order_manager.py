import sqlite3
import json
from backend.app.menu_db import get_menu_data # Assuming menu_db is in the same folder

class OrderManager:
    def __init__(self, db_path="menu.db"):
        self.db_path = db_path
        self.current_order = [] # List of dicts: {"item_id": "...", "name": "...", "quantity": 1, "price": "...", "options": {}, "sides": []}
        self.menu = get_menu_data(db_path=self.db_path) # Load menu from DB

    def _get_item_details(self, item_id):
        for category in self.menu['categories']:
            for item in category['items']:
                if item['id'] == item_id:
                    return item
        return None

    def add_item(self, item_id, quantity=1, options=None, sides=None):
        item_details = self._get_item_details(item_id)
        if not item_details:
            return False, "Item not found."

        # Validate options and sides against menu
        valid_options = True
        if options:
            for opt_type, opt_value in options.items():
                if opt_type not in item_details.get('options', {}) or opt_value not in item_details['options'][opt_type]:
                    valid_options = False
                    break
        if not valid_options:
            return False, f"Invalid option(s) for {item_details['name']}."

        valid_sides = True
        if sides:
            for side in sides:
                if side not in item_details.get('available_sides', []):
                    valid_sides = False
                    break
        if not valid_sides:
            return False, f"Invalid side(s) for {item_details['name']}."


        new_item = {
            "item_id": item_id,
            "name": item_details['name'],
            "price": item_details['price'],
            "quantity": quantity,
            "options": options if options else {},
            "sides": sides if sides else item_details.get('default_sides', [])
        }
        self.current_order.append(new_item)
        return True, f"Added {quantity} {item_details['name']} to order."

    def remove_item(self, item_id):
        initial_len = len(self.current_order)
        # Remove all instances of the item_id
        self.current_order = [item for item in self.current_order if item["item_id"] != item_id]
        if len(self.current_order) < initial_len:
            return True, f"Removed all instances of {item_id.replace('_', ' ').title()} from order."
        return False, "Item not found in order."

    def get_order_summary(self):
        total_price = sum(item['price'] * item['quantity'] for item in self.current_order)
        return {
            "items": self.current_order,
            "total": round(total_price, 2)
        }

    def clear_order(self):
        self.current_order = []
        return True, "Order cleared."

    def finalize_order(self):
        if not self.current_order:
            return False, "Order is empty."
        # In a real system, this would save to a persistent order history,
        # send to kitchen, etc. For now, just return summary and clear.
        summary = self.get_order_summary()
        self.clear_order() # Clear after finalizing
        return True, f"Order finalized. Total: ${summary['total']:.2f}. Thank you!"

    # Add a method to update menu data if it changes
    def update_menu(self):
        self.menu = get_menu_data(db_path=self.db_path)
