from src.models import db, FoodItem
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
        if current_user.is_authenticated:
            return FoodItem.query.filter_by(user_id=current_user.id).all()
        else:
            return []

    def calculate_costs(self):
        results = []
        for item in self.get_food_items():
            protein_cost = item.cost_per_gram_of_macronutrient('protein')
            fat_cost = item.cost_per_gram_of_macronutrient('fat')
            carb_cost = item.cost_per_gram_of_macronutrient('carb')
            results.append({
                'name': item.name,
                'protein_cost': protein_cost,
                'fat_cost': fat_cost,
                'carb_cost': carb_cost
            })
        return results

    def find_cheapest_macronutrient(self, macronutrient):
        available_items = [
            item for item in self.get_food_items()
            if item.cost_per_gram_of_macronutrient(macronutrient) is not None
        ]
        if not available_items:
            return None, None
        cheapest_item = min(
            available_items,
            key=lambda item: item.cost_per_gram_of_macronutrient(macronutrient)
        )
        return cheapest_item, cheapest_item.cost_per_gram_of_macronutrient(macronutrient)

    def calculate_macronutrient_needs(self, user):
        total_calories = user.daily_calories
        protein_calories = total_calories * (user.protein_percentage / 100)
        fat_calories = total_calories * (user.fat_percentage / 100)
        carb_calories = total_calories * (user.carb_percentage / 100)

        protein_grams = protein_calories / 4
        fat_grams = fat_calories / 9
        carb_grams = carb_calories / 4

        return {
            'protein': protein_grams,
            'fat': fat_grams,
            'carb': carb_grams
        }

    def calculate_total_cost(self):
        macronutrient_needs = self.calculate_macronutrient_needs(current_user)

        priority_order = current_user.priority_order.split(" > ")
        total_cost = 0
        selected_foods = {}

        # Initialize grams needed for each macronutrient
        remaining_needs = macronutrient_needs.copy()

        for macro in priority_order:
            if remaining_needs[macro] > 0:
                item, cost_per_gram = self.find_cheapest_macronutrient(macro)
                if item and cost_per_gram:
                    grams_needed = remaining_needs[macro]
                    multiplier = grams_needed / item.macro_content_per_unit(macro)

                    remaining_needs["protein"] = remaining_needs["protein"] - (item.macro_content_per_unit("protein") * multiplier)
                    remaining_needs["carb"] = remaining_needs["carb"] - (item.macro_content_per_unit("carb") * multiplier)
                    remaining_needs["fat"] = remaining_needs["fat"] - (item.macro_content_per_unit("fat") * multiplier)

                    # Calculate total weight
                    total_item_weight = multiplier * item.unit_weight

                    cost = grams_needed * float(cost_per_gram)
                    total_cost += cost

                    selected_foods[macro] = {
                        'food': item.name,
                        'grams_needed': grams_needed,
                        'cost': cost,
                        'total_weight': total_item_weight,
                    }

        return {
            'total_cost': total_cost,
            'details': selected_foods
        }
