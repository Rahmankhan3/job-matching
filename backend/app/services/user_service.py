from app.database import users_collection
from app.models.user import User, UserInDB, UserRole
from app.utils.password import hash_password, verify_password
from typing import Optional
from bson import ObjectId
from datetime import datetime


async def create_user(email: str, password: str, role: str) -> Optional[User]:

    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        return None 

    hashed_password = hash_password(password)

    user_doc = {
        "email": email,
        "password_hash": hashed_password,
        "role": role,
        "created_at": datetime.utcnow()
    }

    result = await users_collection.insert_one(user_doc)

    if result.inserted_id:
        
        created_user = await users_collection.find_one(
            {"_id": result.inserted_id},
            {"password_hash": 0} # 0 suggests that password is excluded
        )

        # MongoDB stores _id as ObjectId, but our Pydantic model expects id as str
        # So we pop "_id", convert to string, and assign to "id"
        created_user["id"] = str(created_user.pop("_id"))
        return User(**created_user)

    return None


async def get_user_by_email(email: str) -> Optional[User]:

    user_doc = await users_collection.find_one(
        {"email": email},
        {"password_hash": 0}    # exclude password from public-facing lookups
    )

    if user_doc:
        user_doc["id"] = str(user_doc.pop("_id"))
        return User(**user_doc)
    return None


async def get_user_by_id(user_id: str) -> Optional[User]:

    try:
        # ObjectId() will throw if user_id is not a valid MongoDB ObjectId format
        user_doc = await users_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"password_hash": 0}
        )
    except Exception:
       
        return None
    if user_doc:
        user_doc["id"] = str(user_doc.pop("_id"))
        return User(**user_doc)

    return None


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:


   
    user_doc = await users_collection.find_one({"email": email})

    if not user_doc:
        return None 

    if not verify_password(password, user_doc["password_hash"]):
        return None  

    user_doc["id"] = str(user_doc.pop("_id"))
    return UserInDB(**user_doc)
