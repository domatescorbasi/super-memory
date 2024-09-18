import re
import requests
from src.models import FoodItem


class FoodItemScraper:
    SEARCH_URL = 'https://fdc.nal.usda.gov/portal-data/external/search'
    ITEM_URL_TEMPLATE = 'https://fdc.nal.usda.gov/portal-data/external/{}'

    HEADERS = {
        'Host': 'fdc.nal.usda.gov',
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://fdc.nal.usda.gov'
    }

    def __init__(self, item_id=None):
        self.item_id = item_id

    def search(self, query, page_number=1):
        payload = {
            "includeDataTypes": {"Foundation": True},
            "referenceFoodsCheckBox": True,
            "requireAllWords": True,
            "generalSearchInput": query,
            "pageNumber": page_number,
            "sortCriteria": {
                "sortColumn": "description",
                "sortDirection": "asc"
            }
        }
        response = requests.post(self.SEARCH_URL, headers=self.HEADERS, json=payload)
        if response.status_code == 200:
            data = response.json()
            return self.extract_search_results(data)
        else:
            print(f"Search request failed with status code: {response.status_code}")
            return []

    def extract_search_results(self, data):
        foods = data.get('foods', [])
        results = []
        for food in foods:
            fdcId = food.get('fdcId')
            description = food.get('description')
            results.append((fdcId, description))
        return results

    def fetch_data(self, item_id):
        api_url = self.ITEM_URL_TEMPLATE.format(item_id)
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to retrieve data for item {item_id}")
            return None

    def parse_data(self, data):
        if not data:
            return None

        description = data.get('description', 'Unknown food item')
        food_nutrients = data.get('foodNutrients', [])

        water = protein = fat = carbs = 0

        for nutrient in food_nutrients:
            nutrient_info = nutrient.get('nutrient', {})
            nutrient_name = nutrient_info.get('name', '').lower()


            if 'protein' in nutrient_name:
                protein = nutrient.get('value', 0)
            elif 'total lipid (fat)' in nutrient_name:
                fat = nutrient.get('value', 0)
            elif 'carbohydrate, by difference' in nutrient_name:
                carbs = nutrient.get('value', 0)
            elif 'water' == nutrient_name:
                water = nutrient.get('value', 0)

        return FoodItem(
            name=description,
            protein=protein,
            fat=fat,
            carbs=carbs,
            price_per_unit=0,
            unit_weight=round((water + fat + carbs + protein), 2)
        )

    def scrape(self, item_id=None):
        if item_id:
            data = self.fetch_data(item_id)
            if data:
                return self.parse_data(data)
        elif self.item_id:
            data = self.fetch_data(self.item_id)
            if data:
                return self.parse_data(data)
        else:
            raise ValueError("Item ID is required to scrape data.")
        return None

    def extract_item_id_from_url(self, url):
        match = re.search(r'/food-details/(\d+)/nutrients', url)
        if match:
            return match.group(1)
        else:
            return None
