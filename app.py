from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import get_db, init_db

app = FastAPI(title="MCP Bank Server")

# initialize db on start
init_db()

class Account(BaseModel):
    name: str

class Transaction(BaseModel):
    account_id: int
    amount: float

TOKEN = "secure-key-123"  # simple security token

# Security middleware
def auth(token: str):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/create_account")
def create_account(acc: Account, token: str):
    auth(token)
    conn = get_db()
    cursor = conn.execute("INSERT INTO accounts (name) VALUES (?)", (acc.name,))
    conn.commit()
    return {"message": "Account created", "account_id": cursor.lastrowid}

@app.post("/deposit")
def deposit(data: Transaction, token: str):
    auth(token)
    conn = get_db()
    conn.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (data.amount, data.account_id))
    conn.execute("INSERT INTO transactions (account_id, type, amount) VALUES (?, 'deposit', ?)", (data.account_id, data.amount))
    conn.commit()
    return {"message": "Deposit successful"}

@app.post("/withdraw")
def withdraw(data: Transaction, token: str):
    auth(token)
    conn = get_db()
    bal = conn.execute("SELECT balance FROM accounts WHERE id=?", (data.account_id,)).fetchone()
    if bal is None or bal["balance"] < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    conn.execute("UPDATE accounts SET balance = balance - ? WHERE id=?", (data.amount, data.account_id))
    conn.execute("INSERT INTO transactions (account_id, type, amount) VALUES (?, 'withdraw', ?)", (data.account_id, data.amount))
    conn.commit()
    return {"message": "Withdrawal successful"}

@app.get("/balance/{account_id}")
def balance(account_id: int, token: str):
    auth(token)
    conn = get_db()
    bal = conn.execute("SELECT balance FROM accounts WHERE id=?", (account_id,)).fetchone()
    if bal is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"balance": bal["balance"]}

@app.get("/transactions/{account_id}")
def transactions(account_id: int, token: str):
    auth(token)
    conn = get_db()
    txns = conn.execute("SELECT * FROM transactions WHERE account_id=? ORDER BY timestamp DESC LIMIT 10", (account_id,)).fetchall()
    return {"transactions": [dict(row) for row in txns]}

@app.get("/")
def home():
    return {"message": "MCP Bank Server Running Successfully!"}
