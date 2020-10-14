
from typing import Optional
from fastapi import HTTPException, status, Response

from app import account_collection
from app.utilities.encryption import generate_password_hash, \
    check_password_hash, generate_secret_token, validate_password_format
from app.utilities.mailing import send_verification_mail


async def get_account(email: str):
    account = await account_collection.find_one({"email": email})
    # I don't wall all data in the database to be part of the returned model!
    return {
        'email': account["email"],
        "email_verified": account["email_verified"]
    }


async def create_account(email: str, password: str):

    if not validate_password_format(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="password format invalid",
        )

    account_model = {
        "email": email,
        "hashed_password": generate_password_hash(password),
        "email_token": generate_secret_token(length=32),
        "email_verified": False
    }

    try:
        # collection has a unique index on "email"
        # -> trying to insert a mail that already exists
        # will result in an error
        await account_collection.insert_one(account_model)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already taken",
        )

    try:
        await send_verification_mail(account_model)
    except AssertionError:
        await account_collection.delete_one({"email": email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"verification could not be sent",
        )

    return {
        "email": email,
        "email_verified": False
    }


async def verify_account(email_token: str, password: str):
    try:
        account = await account_collection.find_one({"email_token": email_token})
        assert(account is not None)
        assert(check_password_hash(password, account["hashed_password"]))
        await account_collection.update_one(
            {"email_token": email_token},
            {'$set': {'email_verified': True}}
        )
        return {"status": "success"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email_token or password invalid",
        )


async def change_password(account, old_password, new_password):
    if not account["email_verified"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email address not verified yet",
        )

    if not validate_password_format(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_password format invalid",
        )

    db_account = await account_collection.find_one({"email": account["email"]})

    if not check_password_hash(old_password, db_account["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="old_password invalid",
        )

    await account_collection.update_one(
        {"email": account["email"]},
        {"$set": {"hashed_password": generate_password_hash(new_password)}}
    )

    return {"status": "success"}