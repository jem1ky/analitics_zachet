# DataScope Analytics

DataScope Analytics is a browser-based analytics project built completely in Python. The application loads sales data, cleans it, filters it, builds charts and generates a short analytical summary.

## Stack

- Streamlit
- pandas
- numpy
- plotly
- matplotlib
- pytest

## Features

- CSV upload or built-in sample dataset
- Data cleaning and validation
- Filtering by date, region, category and product
- 3 interactive charts and 1 additional histogram
- Analytical summary with key metrics
- Export of filtered dataset and summary
- Error handling for invalid files
- Automated tests

## Project structure

```text
project_NOW/
+-- app/
|   +-- config/
|   +-- models/
|   +-- routes/
|   +-- services/
|   `-- utils/
+-- data/
+-- tests/
`-- main.py
```

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

## Testing

```bash
python -m pytest
```

## Dataset requirements

The uploaded CSV should contain these columns:

- `date`
- `region`
- `category`
- `product`
- `sales`
- `profit`
- `orders`
- `customer_rating`

If no file is uploaded, the app generates and uses a built-in sample dataset automatically.
