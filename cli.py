import requests

BASE_URL = "http://127.0.0.1:5000"


def api(method, path, **kwargs):
    try:
        response = getattr(requests, method)(f"{BASE_URL}{path}", **kwargs)
    except requests.RequestException:
        print("[!] Could not connect to the Flask API. Is app.py running?")
        return None
    if not 200 <= response.status_code < 300:
        print("Error:", response.json().get("error", "Request failed"))
        return None
    return response


def print_menu():
    print("\n=== Inventory Management CLI ===")
    print("1. View inventory  2. View item  3. Add item")
    print("4. Add by barcode  5. Update item  6. Delete item  7. Exit")


def view_all():
    response = api("get", "/inventory")
    if response is None:
        return
    items = response.json()
    if not items:
        print("Inventory is empty.")
    for item in items:
        stock = item.get("stock", item.get("stock_quantity", 0))
        print(f"{item['id']} | {item['product_name']} | {item['brands']} | ${item['price']:.2f} | Stock: {stock}")


def view_one():
    item_id = input("Item ID: ").strip()
    response = api("get", f"/inventory/{item_id}")
    if response:
        item = response.json()
        stock = item.get("stock", item.get("stock_quantity", 0))
        print(f"{item['id']} | {item['product_name']} | {item['brands']}\n"
              f"{item['ingredients_text']} | ${item['price']:.2f} | Stock: {stock}")


def number(prompt, convert):
    try:
        return convert(input(prompt) or 0)
    except ValueError:
        print("[!] Enter a valid number.")
        return None


def add_manual():
    item_id = input("ID: ").strip()
    name = input("Product name: ").strip()
    brand = input("Brand: ").strip() or "N/A"
    ingredients = input("Ingredients: ").strip() or "N/A"
    price, stock = number("Price: ", float), number("Stock: ", int)
    if price is None or stock is None:
        return
    item = {"id": item_id, "product_name": name, "brands": brand,
            "ingredients_text": ingredients, "price": price, "stock": stock}
    if api("post", "/inventory", json=item):
        print(f"Added '{name}' to inventory.")


def add_from_barcode():
    barcode = input("Barcode: ").strip()
    if not barcode:
        print("[!] Barcode cannot be empty.")
        return
    response = api("get", f"/external/fetch/{barcode}")
    if response is None:
        return
    product = response.json()
    print(f"Found: {product['product_name']} ({product['brands']})")
    item_id = input("Local ID: ").strip()
    price, stock = number("Selling price: ", float), number("Initial stock: ", int)
    if price is None or stock is None:
        return
    item = {"id": item_id, **product, "price": price, "stock": stock}
    if api("post", "/inventory", json=item):
        print("Product added to inventory.")


def update_item():
    item_id = input("Item ID: ").strip()
    price = input("New price (blank to skip): ").strip()
    stock = input("New stock (blank to skip): ").strip()
    try:
        changes = {}
        if price:
            changes["price"] = float(price)
        if stock:
            changes["stock"] = int(stock)
    except ValueError:
        print("[!] Enter valid numbers.")
        return
    if not changes:
        print("[!] No changes provided.")
    elif api("patch", f"/inventory/{item_id}", json=changes):
        print("Item updated successfully.")


def delete_item():
    item_id = input("Item ID: ").strip()
    if input(f"Delete {item_id}? (y/N): ").strip().lower() != "y":
        print("Deletion canceled.")
        return
    response = api("delete", f"/inventory/{item_id}")
    if response:
        print(response.json().get("message"))


def main():
    actions = {"1": view_all, "2": view_one, "3": add_manual,
               "4": add_from_barcode, "5": update_item, "6": delete_item}
    while True:
        print_menu()
        choice = input("Choose 1-7: ").strip()
        if choice == "7":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("[!] Invalid choice.")


if __name__ == "__main__":
    main()

