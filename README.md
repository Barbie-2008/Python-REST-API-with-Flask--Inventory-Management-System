# Flask Inventory Management System

A small Flask API and command-line interface for managing inventory. Inventory is stored in memory and resets when the server restarts.

## Installation and Setup

Requires Python 3.12 and Pipenv.

```bash
python -m pip install pipenv
pipenv install
```

Start the API in one terminal:

```bash
pipenv run python app.py
```

Start the CLI in another terminal:

```bash
pipenv run python cli.py
```

Run the tests with:

```bash
pipenv run pytest
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/inventory` | List all inventory items. |
| GET | `/inventory/<item_id>` | Get one item by ID. |
| POST | `/inventory` | Add an item. Requires `id`, `product_name`, `brands`, `ingredients_text`, `price`, and `stock` (or `stock_quantity`). |
| PATCH | `/inventory/<item_id>` | Update supplied item fields. |
| DELETE | `/inventory/<item_id>` | Delete an item. |
| GET | `/external/fetch/<barcode>` | Look up product details from OpenFoodFacts. |

Example: add an item with `curl`:

```bash
curl -X POST http://127.0.0.1:5000/inventory \
	-H 'Content-Type: application/json' \
	-d '{"id":"201","product_name":"Yogurt","brands":"Example","ingredients_text":"Milk","price":2.50,"stock":10}'
```

## CLI Examples

Run `pipenv run python cli.py`, then choose an option from the menu:

- `1`: View all inventory
- `2`: View an item by ID
- `3`: Add an item manually
- `4`: Find a product by barcode and add it to inventory
- `5`: Update an item's price or stock
- `6`: Delete an item
- `7`: Exit

For barcode lookup, enter the barcode, then provide a local ID, selling price, and starting stock when prompted.

## Comments and Maintainability

Keep comments focused on non-obvious decisions; use clear function names for self-explanatory code. When changing an endpoint or CLI workflow, update its tests and this endpoint or menu list. The inventory currently uses an in-memory list, so data is not persistent between server runs.

## Push to GitHub

1. Create an empty repository on GitHub. 
2. Add and commit the project files:

	```bash
	git add .
	git commit -m "Build Flask inventory management API"
	```

3. Push the feature branch:

	```bash
	git push -u origin feature/flask-api
	```

4. On GitHub, open a pull request from `feature/flask-api` into `main`. Merge it, then delete the feature branch if it is no longer needed.