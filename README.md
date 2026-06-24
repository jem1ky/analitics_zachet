# DataScope Analytics

DataScope Analytics is a browser-based analytics project built in Python and adapted for deployment on Vercel. The application loads sales data, cleans it, filters it, builds charts and generates a short analytical summary.

## Stack

- Flask
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
- Vercel-compatible Python entrypoint

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
+-- templates/
+-- tests/
`-- main.py
```

## Run locally

```bash
python -m pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:5000` in your browser.

## Vercel deployment

The project is prepared for Vercel's official Python runtime. Vercel detects the `Flask` app instance named `app` from `main.py`.

You can deploy with:

```bash
vercel
vercel --prod
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
