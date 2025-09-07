from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import websockets
import json
import asyncio

APP_ID = 99309  # Your Deriv App ID
BACKEND_URL = "http://localhost:8000"  # Change later when deployed
REDIRECT_URL = f"{BACKEND_URL}/callback"

app = FastAPI()
tokens = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>Destroyer Bot Backend</h1>
    <p>Use the frontend site to login & trade.</p>
    """

@app.get("/login")
async def login():
    login_url = f"https://oauth.deriv.com/oauth2/authorize?app_id={APP_ID}&scope=read,trade&redirect_uri={REDIRECT_URL}"
    return RedirectResponse(url=login_url)

@app.get("/callback")
async def callback(request: Request):
    params = dict(request.query_params)
    auth_token = params.get("token")

    if not auth_token:
        return {"error": "No token received"}

    tokens["current"] = auth_token
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    if "current" not in tokens:
        return RedirectResponse(url="/login")

    return """
    <h2>Destroyer Dashboard (Backend)</h2>
    <p>✅ Logged in successfully</p>
    <a href="/balance">Check Balance</a><br>
    <a href="/trade">Run Test Trade</a>
    """

@app.get("/balance")
async def balance():
    if "current" not in tokens:
        return {"error": "Not logged in"}

    async with websockets.connect("wss://ws.derivws.com/websockets/v3?app_id=" + str(APP_ID)) as ws:
        await ws.send(json.dumps({"authorize": tokens["current"]}))
        await ws.recv()

        await ws.send(json.dumps({"balance": 1}))
        response = await ws.recv()
        data = json.loads(response)
        balance = data.get("balance", {}).get("balance", "Unknown")

        return {"balance": balance}

@app.get("/trade")
async def trade():
    if "current" not in tokens:
        return {"error": "Not logged in"}

    async with websockets.connect("wss://ws.derivws.com/websockets/v3?app_id=" + str(APP_ID)) as ws:
        await ws.send(json.dumps({"authorize": tokens["current"]}))
        await ws.recv()

        contract = {
            "buy": 1,
            "parameters": {
                "amount": 1,
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": "R_100"
            }
        }

        await ws.send(json.dumps(contract))
        response = await ws.recv()
        data = json.loads(response)

        return {"trade_response": data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
