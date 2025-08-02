from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ AQLIFY BACKEND WORKING!", "status": "success", "working": True}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    return "\n".join([f"- {item['date']}: {item['quantity']} units" for item in history])

# --- Login --- 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Hardcoded credentials for MVP testing
ADMIN_EMAIL = "expert@aqlify.com"
ADMIN_PASSWORD = "forecast2025"

# Temporary demo account for ChatGPT access
DEMO_EMAIL = "demo@aqlify.com"
DEMO_PASSWORD = "demo2025"

@app.post("/login")
async def login(req: LoginRequest):
    # Securely compare credentials to prevent timing attacks
    is_admin = secrets.compare_digest(req.email.lower(), ADMIN_EMAIL) and secrets.compare_digest(req.password, ADMIN_PASSWORD)
    is_demo = secrets.compare_digest(req.email.lower(), DEMO_EMAIL) and secrets.compare_digest(req.password, DEMO_PASSWORD)

    if not (is_admin or is_demo):
        raise HTTPException(
            status_code=401,
            detail="Invalid login. Please check your email and password."
        )
    
    # Return user type in response
    return {
        "message": "Login successful",
        "userType": "admin" if is_admin else "demo"
    }


@app.post("/forecast", response_model=ForecastResponse)
async def forecast(req: ForecastRequest):
    if not req.sales_data or len(req.sales_data) < 14:
        raise HTTPException(status_code=400, detail="At least 14 days of sales data are required.")

    history_dicts = [e.dict() for e in req.sales_data]
    formatted_history = format_sales_history(history_dicts)
    last_14_days = history_dicts[-14:]
    avg_14_day_sales = sum(item['quantity'] for item in last_14_days) / 14

    system_prompt = """You are an expert AI demand forecasting assistant for supply chain managers in Oman.
Your analysis must be sharp, context-aware, and actionable.
Always respond in valid JSON."""

    notes_section = f"""    Additional Notes from User:
    {req.user_notes}
""" if req.user_notes else ""

    user_prompt = f"""
    Context:
    - Product Type: {req.product_type}
    - Region: {req.region}
    - Selling Point: {req.selling_point}
{notes_section}
    Sales history:
    {formatted_history}

    14-day average daily sales: {avg_14_day_sales:.2f}

    Instructions:
    1. Analyze the provided sales history and user notes to identify trends, seasonality, and any obvious spikes or dips.
    2. Consider the context:
        - Product Type ({req.product_type}): Certain products have unique demand patterns (e.g., medical supplies vs. consumer goods).
        - Region ({req.region}): Demand can vary significantly by region in Oman. Consider local events or demographics.
        - Selling Point ({req.selling_point}): The sales channel (e.g., retail vs. wholesale) heavily influences sales volume and patterns.
        - User Notes: Pay close attention to any specific insights, events, or promotions mentioned in the notes.
    3. Generate a 30-day demand forecast. Use the 14-day average as a baseline but adjust it based on your analysis of trends and context.
    4. Provide a detailed English summary explaining your forecast. Justify your reasoning by referencing the sales data, the provided context, and user notes.
    5. Provide a one-sentence summary in Arabic.
    6. Suggest a reorder quantity, assuming a 7-day lead time and a 7-day safety stock buffer.
    7. Provide a forecast confidence level (High, Medium, or Low) and a brief justification.

    Respond with a JSON object with this exact structure:
    {{
      "forecasts": [{{ "forecast_date": "YYYY-MM-DD", "forecast_qty": integer }}],
      "reorder_qty": "string",
      "confidence": "string",
      "english_summary": "string",
      "arabic_summary": "string"
    }}
    """

    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OpenAI API key not set.")
            raise HTTPException(status_code=500, detail="OpenAI API key not set.")

        client = OpenAI(api_key=api_key)
        
        print("Sending request to OpenAI API with new context...")
        start_time = time.time()

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        end_time = time.time()
        print(f"Received response from OpenAI API in {end_time - start_time:.2f} seconds.")

        forecast_data = json.loads(response.choices[0].message.content)
        print("Successfully parsed JSON response.")
        return forecast_data

    except json.JSONDecodeError:
        print("ERROR: Failed to decode JSON from OpenAI response.")
        raise HTTPException(status_code=500, detail="AI failed to return valid JSON.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
