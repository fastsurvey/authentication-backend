
from typing import Optional
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException, status, Form
from datetime import datetime, timedelta

from app import app, ENVIRONMENT, PUBLIC_KEY, oauth2_scheme

from app.utilities.authentication import \
    authenticate_from_login, authenticate_from_access_token, \
    authenticate_from_refresh_token
from app.utilities.account_functions import \
    create_account, verify_account, change_password, \
    forgot_password, restore_forgotten_password
from app.utilities.encryption import generate_oauth_token
import time


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class Account(BaseModel):
    email: str
    email_verified: bool


@app.get('/')
def index_route():
    return {
        "status": "healthy",
        "mode": ENVIRONMENT,
        "public_key": PUBLIC_KEY
    }


@app.post("/login/form")
async def login_form_route(
    email: str = Form(...),
    password: str = Form(...)
):
    account = await authenticate_from_login(email, password)
    return {
        "jwt": generate_oauth_token(account),
        "account": account
    }


@app.post("/login/access")
async def login_access_token_route(
    access_token: str = Form(...)
):
    # Don't need to generate a new jwt when the access_token is still valid
    account = await authenticate_from_access_token(access_token)
    return {
        "account": account
    }


@app.post("/login/refresh")
async def login_refresh_token_route(
    refresh_token: str = Form(...)
):
    account = await authenticate_from_refresh_token(refresh_token)
    return {
        "jwt": generate_oauth_token(account),
        "account": account
    }


@app.post('/register')
async def register_route(
    email: str = Form(...),
    password: str = Form(...)
):
    account = await create_account(email, password)
    return {
        "jwt": generate_oauth_token(account),
        "account": account
    }


@app.post('/verify')
async def verify_route(
    email_token: str = Form(...),
    password: str = Form(...)
):
    return await verify_account(email_token, password)


@app.get("/account", response_model=Account)
async def account_route(
    access_token: str = Depends(oauth2_scheme)
):
    return await authenticate_from_access_token(access_token)


@app.post('/change-password')
async def change_password_route(
    access_token: str = Depends(oauth2_scheme),
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    account = await authenticate_from_access_token(access_token)
    return await change_password(account, old_password, new_password)


@app.post('/forgot-password')
async def change_password_route(
    email: str = Form(...)
):
    return await forgot_password(email)


@app.post('/restore-forgotten-password')
async def change_password_route(
    forgot_password_token: str = Form(...),
    new_password: str = Form(...)
):
    return await restore_forgotten_password(forgot_password_token, new_password)
