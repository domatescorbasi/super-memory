from models import db, FoodItem
from flask_login import current_user

class FoodCalculator:
    def __init__(self, app):
        db.init_app(app)
        with app.app_context():
            db.create_all()

    def add(self, food_item):
        db.session.add(food_item)
        db.session.commit()

    def get_food_items(self):
        # Get food items that belong to the currently logged-in user
        if current_user.is_authenticated:
            return FoodItem.query.filter_by(user_id=current_user.id).all()
        else:
            return []

    def calculate_costs(self):
        results = []
        for item in self.get_food_items():
            protein_cost = item.cost_per_gram_of_macronutrient('protein')
            fat_cost = item.cost_per_gram_of_macronutrient('fat')
            carbs_cost = item.cost_per_gram_of_macronutrient('carbs')
            results.append({
                'name': item.name,
                'protein_cost': protein_cost,
                'fat_cost': fat_cost,
                'carbs_cost': carbs_cost
            })
        print(results)
        return results

    def find_cheapest_macronutrient(self, macronutrient):
        available_items = [item for item in self.get_food_items() if
                           item.cost_per_gram_of_macronutrient(macronutrient) is not None]
        if not available_items:
            return None, None
        cheapest_item = min(available_items, key=lambda item: item.cost_per_gram_of_macronutrient(macronutrient))
        return cheapest_item.name, cheapest_item.cost_per_gram_of_macronutrient(macronutrient)
