# main.py
import os
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from passlib.context import CryptContext
from jose import jwt, JWTError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MASTER_DB = os.getenv("MASTER_DB", "master_db")
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))

client = MongoClient(MONGO_URI)
master_db = client[MASTER_DB]
orgs_col = master_db["organizations"]
admins_col = master_db["admins"]

# Using Argon2 to avoid bcrypt issues (72 byte)
pwd_ctx = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# security scheme for SwaggerUI
security = HTTPBearer()

app = FastAPI(
    title="Org Management Service (assignment)",
    swagger_ui_parameters={"persistAuthorization": True},
    components={
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
)

def sanitize_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_\-]", "", s)
    return s

def get_collection_name(org_name: str) -> str:
    return f"org_{sanitize_name(org_name)}"

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_jwt(payload: dict, expires_seconds: Optional[int] = None) -> str:
    to_encode = payload.copy()
    expire = datetime.utcnow() + timedelta(seconds=(expires_seconds or JWT_EXP_SECONDS))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

#Pydantic Models
class CreateOrgRequest(BaseModel):
    organization_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UpdateOrgRequest(BaseModel):
    organization_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

#POST/org/create
@app.post("/org/create")
def create_org(req: CreateOrgRequest):
    name = req.organization_name.strip()

    # check duplicates
    if orgs_col.find_one({"organization_name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}):
        raise HTTPException(status_code=400, detail="Organization name already exists")

    #admin user
    admin_doc = {
        "email": req.email,
        "password_hash": hash_password(req.password),
        "created_at": datetime.utcnow()
    }
    admin_result = admins_col.insert_one(admin_doc)
    admin_id = admin_result.inserted_id

    collection_name = get_collection_name(name)
    org_doc = {
        "organization_name": name,
        "collection_name": collection_name,
        "admin_user_id": admin_id,
        "created_at": datetime.utcnow(),
        "deleted": False
    }

    try:
        org_result = orgs_col.insert_one(org_doc)
    except errors.DuplicateKeyError:
        admins_col.delete_one({"_id": admin_id})
        raise HTTPException(status_code=400, detail="Organization name already exists (race)")

    #dynamic collection
    org_collection = master_db[collection_name]
    org_collection.insert_one({"_init": True, "created_at": datetime.utcnow()})

    return {
        "message": "Organization created successfully",
        "organization_id": str(org_result.inserted_id),
        "organization_name": name,
        "collection_name": collection_name,
        "admin_email": req.email
    }

@app.post("/admin/login")
def admin_login(req: AdminLoginRequest):
    admin = admins_col.find_one({"email": req.email})
    if not admin or not verify_password(req.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    org = orgs_col.find_one({"admin_user_id": admin["_id"], "deleted": False})
    org_id = str(org["_id"]) if org else None

    payload = {"admin_id": str(admin["_id"]), "org_id": org_id, "email": admin["email"]}
    token = create_jwt(payload)

    return {"access_token": token, "token_type": "bearer", "organization_id": org_id}

@app.get("/org/get")
def get_org(organization_name: str):
    org = orgs_col.find_one({
        "organization_name": {"$regex": f"^{re.escape(organization_name.strip())}$", "$options": "i"}
    })
    if not org or org.get("deleted"):
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "organization_id": str(org["_id"]),
        "organization_name": org["organization_name"],
        "collection_name": org["collection_name"]
    }

#token decode
def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return decode_jwt(token)

#DELETE Function
@app.delete("/org/delete")
def delete_org(organization_name: str, current=Depends(get_current_admin)):
    token_org_id = current.get("org_id")

    org = orgs_col.find_one({
        "organization_name": {"$regex": f"^{re.escape(organization_name.strip())}$", "$options": "i"}
    })

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if token_org_id != str(org["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this org")

    orgs_col.update_one(
        {"_id": org["_id"]},
        {"$set": {"deleted": True, "deleted_at": datetime.utcnow()}}
    )

    master_db.drop_collection(org["collection_name"])

    return {"message": "Organization deleted (soft) and collection dropped"}

# update organization name
@app.put("/org/update")
def update_org(req: UpdateOrgRequest, current=Depends(get_current_admin)):
    admin = admins_col.find_one({"email": req.email})
    if not admin or not verify_password(req.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # find organization name
    org = orgs_col.find_one({"admin_user_id": admin["_id"], "deleted": False})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    old_name = org["organization_name"]
    new_name = req.organization_name.strip()

    #new name exists then do this
    if orgs_col.find_one({
        "organization_name": {"$regex": f"^{re.escape(new_name)}$", "$options": "i"}
    }):
        raise HTTPException(status_code=400, detail="New organization name already exists")

    old_collection = master_db[org["collection_name"]]
    new_collection_name = get_collection_name(new_name)
    new_collection = master_db[new_collection_name]

    # Copy documents
    docs = list(old_collection.find({}))
    if docs:
        new_collection.insert_many(docs)

    # Update master metadata
    orgs_col.update_one(
        {"_id": org["_id"]},
        {"$set": {
            "organization_name": new_name,
            "collection_name": new_collection_name,
            "updated_at": datetime.utcnow()
        }}
    )

    master_db.drop_collection(org["collection_name"])

    return {
        "message": "Organization updated successfully",
        "old_name": old_name,
        "new_name": new_name,
        "old_collection": org["collection_name"],
        "new_collection": new_collection_name
    }
