# DataScope Analytics

DataScope Analytics is a browser-based analytics project built completely in Python with Streamlit. The application loads sales data, cleans it, filters it, builds charts and generates a short analytical summary.

## Stack

- Streamlit
- pandas
- numpy
- plotly
- matplotlib
- pytest

## Features

- CSV upload or built-in sample dataset
- Separate custom resources with manual row entry
- Import CSV text into named custom resources
- Data cleaning and validation
- Filtering by date, region, category and product
- 3 interactive charts and 1 additional histogram
- Analytical summary with key metrics
- Export of filtered dataset and summary
- Error handling for invalid files
- Automated tests
- Session-based upload handling

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
+-- .streamlit/
+-- tests/
`-- main.py
```

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

Open `http://localhost:8501` in your browser.

## Upload behavior

- A valid uploaded CSV is kept only during the current browser session.
- If the uploaded file is invalid, it is cleared automatically and must be uploaded again.
- After a fresh page reopen, the uploaded file is not kept and should be uploaded again.

## Custom resources

- You can create multiple named resources directly in the sidebar.
- Each resource can be filled by manual row entry or by pasted CSV text.
- Custom resources are separate from the regular `Upload CSV` source.

## Streamlit Community Cloud

The project is ready for deployment to Streamlit Community Cloud from the GitHub repository.

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
