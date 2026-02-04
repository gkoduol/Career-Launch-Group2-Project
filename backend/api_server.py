from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv
from supabase import create_client
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import requests
import random
from pathlib import Path

import logging
logger = logging.getLogger("uvicorn.error")

# Force it to look in the same folder as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

load_dotenv(find_dotenv())

app = FastAPI(title="Group Restaurant Recommender API")

# Supabase Setup
# Using your provided URL
supabaseUrl = 'https://rlngfmrwrthxzactluon.supabase.co'
supabaseKey = os.getenv("SUPABASE_KEY")
supabase = create_client(supabaseUrl, supabaseKey)


# Pydantic Model to fix 422 Validation Errors
class RatingPayload(BaseModel):
    user_id: str
    item_id: str
    rating: int
    item_snapshot: Optional[Dict[str, Any]] = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "https://gkoduol.github.io",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


YELP_API_KEY = os.getenv("YELP_API_KEY")


# --- Helper Functions ---
def make_code(n: int = 6) -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(chars) for _ in range(n))


def yelp_search(location: str, term: str, limit: int = 25):
    if not YELP_API_KEY:
        return {"error": "YELP_API_KEY missing"}, []
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}

    params = {"term": term, "location": location, "limit": limit}

    try:
        res = requests.get(
            "https://api.yelp.com/v3/businesses/search",
            headers=headers,
            params=params,
            timeout=12,
        )
        res.raise_for_status()
        return None, res.json().get("businesses", [])
    except requests.RequestException as e:
        return {"error": f"Yelp request failed: {str(e)}"}, []


def normalize_business(b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "item_id": b.get("id"),
        "name": b.get("name"),
        "rating": b.get("rating"),
        "review_count": b.get("review_count"),
        "price": b.get("price"),
        "url": b.get("url"),
        "image_url": b.get("image_url"),
        "address": " ".join(b.get("location", {}).get("display_address", [])),
    }


# --- API Endpoints ---


@app.get("/")
def root():
    return {"ok": True, "message": "API running. See /docs"}


@app.post("/groups")
def create_group(payload: Dict[str, Any] = Body(None)):
    # We generate the ID first
    groupId = make_code()
    try:
        print(f"--- Attempting to create group: {groupId} ---")

        # Try the insert
        response = supabase.table("groups").insert({"id": groupId, "members": []}).execute()

        # Log the raw response so you can see if it's empty or contains an error object
        print(f"Supabase Response: {response}")

        # Check if data came back empty (Classic RLS symptom)
        if not response.data:
            print("FAILURE: No data returned. RLS Policy is likely blocking writes.")
            return {"error": "Database insert failed (RLS blocking?)"}

        print("SUCCESS: Group created.")
        return {"group_id": groupId}
    except Exception as e:
        # This will print the full error in red/error format in your console
        print(f"EXCEPTION occurred: {e}")
        return {"group_id": f"ERROR-{groupId}", "debug": str(e)}


@app.get("/groups/{group_id}")
def join_group(group_id: str, user_id: str):
    # CHECK SUPABASE FOR GROUP
    res = supabase.table("groups").select("members").eq("id", group_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Group not found")

    members = res.data[0]["members"]
    if user_id not in members:
        members.append(user_id)
        # UPDATE MEMBERS IN SUPABASE
        supabase.table("groups").update({"members": members}).eq("id", group_id).execute()

    # COUNT RATINGS FROM SUPABASE (Table: ratings)
    ratings_res = supabase.table("ratings").select("id", count="exact").eq("group_id", group_id).execute()

    return {
        "group_id": group_id,
        "members": members,
        "ratings_count": ratings_res.count or 0,
    }


@app.get("/groups/{group_id}/items")
def get_items(group_id: str, location: str, term: str = "restaurants"):
    # Check Supabase instead of GROUPS dict
    group_check = supabase.table("groups").select("id").eq("id", group_id).execute()
    if not group_check.data:
        raise HTTPException(status_code=404, detail="Group not found")

    err, businesses = yelp_search(location, term, limit=25)
    if err:
        return err

    items = [normalize_business(b) for b in businesses]
    return {"items": items}


@app.post("/groups/{group_id}/ratings")
def add_rating(group_id: str, payload: RatingPayload):
    # CHECK SUPABASE FOR GROUP
    group_check = supabase.table("groups").select("id").eq("id", group_id).execute()
    if not group_check.data:
        raise HTTPException(status_code=404, detail="Group not found")

    # INSERT RATING INTO SUPABASE
    supabase.table("ratings").insert({
        "group_id": group_id,
        "user_id": payload.user_id,
        "item_id": payload.item_id,
        "rating": payload.rating,
        "item_snapshot": payload.item_snapshot,
    }).execute()

    return {"ok": True}


@app.get("/groups/{group_id}/best")
def best(group_id: str):
    # FETCH RATINGS FROM SUPABASE
    res = supabase.table("ratings").select("*").eq("group_id", group_id).execute()
    ratings = res.data

    if not ratings:
        return {"error": "no ratings yet"}

    by_item = {}
    snap = {}
    for r in ratings:
        item_id = r["item_id"]
        by_item.setdefault(item_id, []).append(r["rating"])
        if item_id not in snap and r.get("item_snapshot"):
            snap[item_id] = r["item_snapshot"]

    best_item_id = None
    best_score = float("-inf")

    for item_id, rs in by_item.items():
        avg = sum(rs) / len(rs)
        mn = min(rs)
        score = avg + (0.5 * mn)
        if score > best_score:
            best_score = score
            best_item_id = item_id

    return {
        "best": {
            "item_id": best_item_id,
            "item": snap.get(best_item_id),
            "score": best_score,
            "ratings_count": len(by_item.get(best_item_id, [])),
        }
    }