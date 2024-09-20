from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    theme_preference = db.Column(db.String(10), default='light')

    # New fields
    daily_calories = db.Column(db.Float, nullable=True)
    protein_percentage = db.Column(db.Float, nullable=True)
    fat_percentage = db.Column(db.Float, nullable=True)
    carb_percentage = db.Column(db.Float, nullable=True)
    priority_order = db.Column(db.String(20), nullable=True)  # Stores priority like "protein > fat > carb"

    food_items = db.relationship('FoodItem', back_populates='user')

    # Methods to update new fields
    def update_profile_macros(self, daily_calories, protein_percentage, fat_percentage, carb_percentage, priority_order):
        self.daily_calories = daily_calories
        self.protein_percentage = protein_percentage
        self.fat_percentage = fat_percentage
        self.carb_percentage = carb_percentage
        self.priority_order = priority_order

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_username(self, new_username):
        self.username = new_username

    def update_password(self, new_password):
        self.set_password(new_password)


class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carb = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    unit_weight = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', back_populates='food_items')

    def __repr__(self):
        return f"<FoodItem {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'protein': self.protein,
            'fat': self.fat,
            'carb': self.carb,
            'price_per_unit': self.price_per_unit,
            'unit_weight': self.unit_weight
        }

    def cost_per_gram_of_macronutrient(self, macronutrient):
        total_macros = self.protein + self.fat + self.carb
        if total_macros == 0:
            return None

        macro_value = getattr(self, macronutrient, 0)
        if macro_value == 0:
            return None

        cost_per_gram_macro_2 = self.price_per_unit / macro_value
        return f"{cost_per_gram_macro_2:,.2f}"

    def macro_content_per_unit(self, macronutrient):
        """Calculate grams of a specific macronutrient per unit."""
        return getattr(self, macronutrient, 0)