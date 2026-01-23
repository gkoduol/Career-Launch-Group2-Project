from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict, Any
import os
import requests
import random

load_dotenv()

app = FastAPI(title="Group Restaurant Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://gkoduol.github.io",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


YELP_API_KEY = os.getenv("YELP_API_KEY")
if not YELP_API_KEY:
    # Server will still start, but Yelp fetch will fail until .env is set
    print("WARNING: YELP_API_KEY is not set. Add it to your .env file.")

# In-memory storage
GROUPS: Dict[str, Dict[str, Any]] = {}


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
        businesses = res.json().get("businesses", [])
        return None, businesses
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


# API endpoints

@app.get("/")
def root():
    return {"ok": True, "message": "API running. See /docs"}


@app.post("/groups")
def create_group():
    gid = make_code()
    GROUPS[gid] = {"members": [], "ratings": []}
    return {"group_id": gid}


@app.get("/groups/{group_id}")
def join_group(group_id: str, user_id: str):
    if group_id not in GROUPS:
        return {"error": "group not found"}

    members = GROUPS[group_id]["members"]
    if user_id not in members:
        members.append(user_id)

    return {
        "group_id": group_id,
        "members": members,
        "ratings_count": len(GROUPS[group_id]["ratings"]),
    }


@app.get("/groups/{group_id}/items")
def get_items(group_id: str, location: str, term: str = "restaurants"):
    if group_id not in GROUPS:
        return {"error": "group not found"}

    err, businesses = yelp_search(location, term, limit=25)
    if err:
        return err

    items = [normalize_business(b) for b in businesses]
    return {"items": items}


@app.post("/groups/{group_id}/ratings")
def add_rating(group_id: str, payload: Dict[str, Any] = Body(...)):
    if group_id not in GROUPS:
        return {"error": "group not found"}

    # Validate required fields
    for k in ("user_id", "item_id", "rating"):
        if k not in payload:
            return {"error": f"missing {k}"}

    try:
        r = int(payload["rating"])
    except Exception:
        return {"error": "rating must be an integer"}

    if r < 1 or r > 5:
        return {"error": "rating must be 1..5"}

    GROUPS[group_id]["ratings"].append(
        {
            "user_id": payload["user_id"],
            "item_id": payload["item_id"],
            "rating": r,
            "item_snapshot": payload.get("item_snapshot"),
        }
    )
    return {"ok": True}


@app.get("/groups/{group_id}/best")
def best(group_id: str):
    if group_id not in GROUPS:
        return {"error": "group not found"}

    ratings = GROUPS[group_id]["ratings"]
    if not ratings:
        return {"error": "no ratings yet"}

    # Aggregate ratings by item_id
    by_item: Dict[str, list] = {}
    snap: Dict[str, Any] = {}

    for r in ratings:
        item_id = r["item_id"]
        by_item.setdefault(item_id, []).append(r["rating"])
        if item_id not in snap and r.get("item_snapshot"):
            snap[item_id] = r["item_snapshot"]

    # Scoring: avg + 0.5*min (balances overall + avoids any "hated" option)
    best_item_id = None
    best_score = float("-inf")
    best_avg = 0.0
    best_min = 0

    for item_id, rs in by_item.items():
        avg = sum(rs) / len(rs)
        mn = min(rs)
        score = avg + 0.5 * mn
        if score > best_score:
            best_score = score
            best_item_id = item_id
            best_avg = avg
            best_min = mn

    return {
        "best": {
            "item_id": best_item_id,
            "item": snap.get(best_item_id),
            "score": best_score,
            "avg": best_avg,
            "min": best_min,
            "ratings_count": len(by_item.get(best_item_id, [])),
        }
    }