from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

#Simulated in-memory database for inventory items
inventory = [
    {
        "id": "101",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "ingredients_text": "Filtered water, organic almonds, organic cane sugar, sea salt",
        "price": 3.99,
        "stock_quantity": 50
    },
    {
        "id": "102",
        "product_name": "Gluten-Free Bread",
        "brands": "Udi's",
        "ingredients_text": "Water, brown rice flour, tapioca starch, potato starch, yeast, sugar, salt, xanthan gum",
        "price": 4.49,
        "stock_quantity": 30
    }
]

# Function to fetch product details from Open Food Facts API
def fetch_product_details(barcode):
    """Query the Open Food Facts API for product details using the barcode."""
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    headers = { "User-Agent": "InventorySystemLab - Python/Flask" }

    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data.get("status") == 1:
        product = data.get("product", {})
        return {
            "product_name": product.get("product_name", "N/A"),
            "brands": product.get("brands", "N/A"),
            "ingredients_text": product.get("ingredients_text", "N/A")
        }
    return None

# RESTful API endpoints for inventory management
# Get all inventory items
@app.route('/inventory', methods=['GET'])
def get_inventory():
    """Return the list of all inventory items."""
    return jsonify(inventory), 200

# Get a specific inventory item by ID
@app.route('/inventory/<item_id>', methods=['GET'])
def get_inventory_item(item_id):
    """Return a specific inventory item by its ID."""
    item = next((item for item in inventory if item["id"] == item_id), None)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404

# Add a new inventory item
@app.route('/inventory', methods=['POST'])
def add_inventory_item():
    """Add a new inventory item to the inventory."""
    data = request.get_json()
    if not data or "id" not in data:
        return jsonify({"error": "Invalid input"}), 400

    # Check if the item already exists
    if any(item["id"] == data["id"] for item in inventory):
        return jsonify({"error": "Item with this ID already exists"}), 400
    stock = data.get("stock", data.get("stock_quantity"))
    if any(field not in data for field in ("product_name", "brands", "ingredients_text", "price")) or stock is None:
        return jsonify({"error": "Invalid input"}), 400

    new_item = {"id": data["id"], "product_name": data["product_name"], "brands": data["brands"], "ingredients_text": data["ingredients_text"], "price": data["price"], "stock_quantity": stock}

    inventory.append(new_item)
    return jsonify(new_item), 201

# Update an existing inventory item
@app.route('/inventory/<item_id>', methods=['PATCH'])
def update_inventory_item(item_id):
    """Update an existing inventory item."""
    item = next((i for i in inventory if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json() or {}
    if "product_name" in data:
        item["product_name"] = data["product_name"]
    if "brands" in data:
        item["brands"] = data["brands"]
    if "ingredients_text" in data:
        item["ingredients_text"] = data["ingredients_text"]
    if "price" in data:
        item["price"] = float(data["price"])
    if "stock" in data or "stock_quantity" in data:
        item["stock_quantity"] = int(data.get("stock", data.get("stock_quantity")))

    response_item = dict(item)
    response_item["stock"] = item["stock_quantity"]
    return jsonify(response_item), 200

# Delete an inventory item
@app.route('/inventory/<item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    """Delete an inventory item by its ID."""
    initial_count = len(inventory)
    inventory[:] = [item for item in inventory if item["id"] != item_id]
    if len(inventory) < initial_count:
        return jsonify({"message": "Item deleted successfully"}), 200
    return jsonify({"error": "Item not found"}), 404

@app.route("/external/fetch/<barcode>", methods=["GET"])
def fetch_external(barcode):
    """Fetch product details from OpenFoodFacts API without adding to database."""
    try:
        data = fetch_product_details(barcode)
    except (requests.RequestException, ValueError):
        return jsonify({"error": "OpenFoodFacts is unavailable."}), 502
    if not data:
        return jsonify({"error": "Product not found on OpenFoodFacts."}), 404
    return jsonify(data), 200


if __name__ == '__main__':
    app.run(debug=True)

