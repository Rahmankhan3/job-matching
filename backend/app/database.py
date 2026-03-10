from pymongo import AsyncMongoClient
from app.config import settings

client = AsyncMongoClient(settings.MONGODB_URL)
database = client[settings.DATABASE_NAME]

users_collection = database["users"]
jobs_collection = database["jobs"]
applications_collection = database["applications"]
candidate_profiles_collection = database["candidate_profiles"]
recruiter_profiles_collection = database["recruiter_profiles"]


async def create_indexes():

    await users_collection.create_index(
        [("email", 1)],
        unique=True
    )

    await jobs_collection.create_index(
        [("recruiter_id", 1)]
    )

    await applications_collection.create_index(
        [("candidate_id", 1)]
    )

    await applications_collection.create_index(
        [("job_posting_id", 1)]
    )

    await applications_collection.create_index(
        [("candidate_id", 1), ("job_posting_id", 1)],
        unique=True
    )

    await candidate_profiles_collection.create_index(
        [("user_id", 1)],
        unique=True
    )

    await recruiter_profiles_collection.create_index(
        [("user_id", 1)],
        unique=True
    )


async def get_database():
    return database