from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from food_calculator import FoodCalculator
from food_scraper import FoodItemScraper
from models import db, FoodItem, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_calculator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bcrypt = Bcrypt(app)
calculator = FoodCalculator(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ----------- HELPER FUNCTIONS ------------ #

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_food_item_by_id(item_id):
    return FoodItem.query.filter_by(id=item_id, user_id=current_user.id).first()


# ----------- AUTHENTICATION ROUTES ------------ #

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user_by_username(username):
            flash('Username already exists', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index_page'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index_page'))
        flash('Login Unsuccessful. Check username and password', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ----------- USER PREFERENCES ------------ #

@app.route('/')
@login_required
def index_page():
    return render_template('index.html', user=current_user)


@app.route('/calculator')
@login_required
def calculator_page():
    return render_template('calculator.html', user=current_user)


@app.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    theme = request.json.get('theme')
    if theme in ['light', 'dark']:
        current_user.theme_preference = theme
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid theme selected'}), 400


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        if new_username:
            current_user.update_username(new_username)
        if new_password:
            current_user.update_password(new_password)
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile_page'))

    return render_template('profile.html')


# Context processor to make user available to all templates
@app.context_processor
def inject_user():
    return dict(user=current_user if current_user.is_authenticated else None)


# Add the following routes if you want API endpoints for profile updates

@app.route('/api/profile/<int:user_id>', methods=['GET'])
@login_required
def get_profile(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({
            'username': user.username,
            'profile_picture': user.profile_picture  # If you have this field
        })
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/profile/<int:user_id>', methods=['PUT'])
@login_required
def update_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json
    if 'username' in data:
        user.update_username(data['username'])
    if 'password' in data:
        user.update_password(data['password'])
    db.session.commit()

    return jsonify({'message': 'Profile updated successfully'})


# ----------- FOOD ITEM MANAGEMENT ------------ #

@app.route('/api/food-items')
@login_required
def api_food_items():
    food_items = FoodItem.query.filter_by(user_id=current_user.id).all()
    return jsonify([item.to_dict() for item in food_items])


@app.route('/api/add-food-item', methods=['POST'])
@login_required
def add_food_item():
    data = request.get_json()
    new_item = FoodItem(
        name=data['name'],
        protein=data['protein'],
        fat=data['fat'],
        carbs=data['carbs'],
        price_per_unit=data['price_per_unit'],
        unit_weight=data['unit_weight'],
        user_id=current_user.id
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Food item added successfully'})


@app.route('/api/edit-food-item/<int:item_id>', methods=['PUT'])
@login_required
def edit_food_item(item_id):
    data = request.get_json()
    food_item = get_food_item_by_id(item_id)
    if food_item:
        food_item.name = data['name']
        food_item.protein = data['protein']
        food_item.fat = data['fat']
        food_item.carbs = data['carbs']
        food_item.price_per_unit = data['price_per_unit']
        food_item.unit_weight = data['unit_weight']
        db.session.commit()
        return jsonify({'message': 'Food item updated successfully'})
    return jsonify({'message': 'Food item not found'}), 404


@app.route('/api/food-items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_food_item(item_id):
    food_item = get_food_item_by_id(item_id)
    if food_item:
        db.session.delete(food_item)
        db.session.commit()
        return jsonify({'message': 'Food item deleted successfully'}), 200
    return jsonify({'message': 'Food item not found or not authorized'}), 404


@app.route('/api/food-items/<int:item_id>', methods=['GET'])
@login_required
def get_food_item(item_id):
    food_item = get_food_item_by_id(item_id)
    if food_item:
        return jsonify(food_item.to_dict())
    return jsonify({'message': 'Food item not found'}), 404


# ----------- FOOD CALCULATOR LOGIC ------------ #

@app.route('/api/calculate-costs', methods=['GET'])
@login_required
def calculate_costs():
    costs = calculator.calculate_costs()
    return jsonify(costs)


@app.route('/api/cheapest-macronutrient', methods=['GET'])
@login_required
def find_cheapest_macronutrient():
    macronutrient = request.args.get('macronutrient')
    item_name, cost = calculator.find_cheapest_macronutrient(macronutrient)
    return jsonify({"cheapest_item": item_name, "cost_per_gram": cost})


# ---------- Scraper ---------------- #


@app.route('/search-food', methods=['POST'])
def search_food():
    data = request.json
    query = data.get('query')

    if query:
        scraper = FoodItemScraper()
        search_results = scraper.search(query=query)
        return jsonify({
            'success': True,
            'results': [{'fdcId': fdcId, 'description': description} for fdcId, description in search_results]
        })
    else:
        return jsonify({'success': False, 'message': 'No query provided.'})

@app.route('/scrape-food', methods=['POST'])
def scrape_food():
    data = request.json
    url = data.get('url')

    if url:
        scraper = FoodItemScraper()
        item_id = scraper.extract_item_id_from_url(url)
        food_item = scraper.scrape(item_id=item_id)

        if food_item:
            return jsonify({
                'success': True,
                'food_item': {
                    'name': food_item.name,
                    'protein': food_item.protein,
                    'fat': food_item.fat,
                    'carbs': food_item.carbs,
                    'unit_weight': food_item.unit_weight
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to scrape food data.'})
    else:
        return jsonify({'success': False, 'message': 'No URL provided.'})
# ----------- RUN THE APPLICATION ------------ #

if __name__ == '__main__':
    app.run(debug=True)
