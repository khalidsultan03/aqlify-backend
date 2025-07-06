# Aqlify Backend

## Setup

1. Copy `.env.example` to `.env` and add your OpenAI API key.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the app:
   ```sh
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API

### POST /forecast

Request body:
```
{
  "item_name": "Paracetamol 500mg",
  "sales_history": [
    { "date": "2025-05-01", "quantity": 20 },
    ...
  ]
}
```

Response:
```
{
  "forecasts": [ { "forecast_date": "2025-07-05", "forecast_qty": 22 }, ... ],
  "reorder_qty": 120,
  "note_arabic": "الطلب مستقر حالياً. ننصح بزيادة المخزون بنسبة 20٪ لتفادي النقص."
}
```
