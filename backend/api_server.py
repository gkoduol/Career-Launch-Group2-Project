from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv
from supabase import create_client
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import random
from pathlib import Path
import logging

# --- Setup & Config ---
logger = logging.getLogger("uvicorn.error")
load_dotenv(find_dotenv())

app = FastAPI(title="Group Restaurant Recommender API")

supabaseUrl = 'https://rlngfmrwrthxzactluon.supabase.co'
supabaseKey = os.getenv("SUPABASE_KEY")
supabase = create_client(supabaseUrl, supabaseKey)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Fallback Images ---
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800",
    "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=800",
    "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800",
    "https://images.unsplash.com/photo-1580822184713-fc5400e7fe10?w=800",
    "https://images.unsplash.com/photo-1526318896980-cf78c088247c?w=800",
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
    "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800",
    "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
    "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800"
]

# --- Models ---
class RatingPayload(BaseModel):
    user_id: str
    item_id: str
    rating: int
    item_snapshot: Optional[Dict[str, Any]] = None

class FinishPayload(BaseModel):
    user_id: str

# --- Helpers ---
def make_code(n: int = 6) -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(chars) for _ in range(n))

def get_consistent_fallback(biz_id: str) -> str:
    if not biz_id: return FALLBACK_IMAGES[0]
    index = sum(ord(char) for char in biz_id) % len(FALLBACK_IMAGES)
    return FALLBACK_IMAGES[index]

def normalize_business(b: Dict[str, Any]) -> Dict[str, Any]:
    raw_address = b.get("location", {}).get("display_address", [])
    clean_address = [str(part) for part in raw_address if part]
    return {
        "item_id": b.get("id"),
        "name": b.get("name"),
        "rating": b.get("rating"),
        "url": b.get("url"),
        "image_url": b.get("image_url"),
        "address": ", ".join(clean_address) if clean_address else "No address provided",
        "categories": b.get("categories"),
    }

# --- Routes ---

@app.get("/")
def root():
    return {"ok": True}

@app.post("/groups")
def create_group(payload: Dict[str, Any] = Body(None)):
    group_id = make_code()
    creator_id = payload.get("user_id", "user_1") 
    try:
        supabase.table("groups").insert({
            "id": group_id, 
            "members": [creator_id],
            "finished_members": []
        }).execute()
        return {"group_id": group_id}
    except Exception as e:
        return {"error": str(e)}

@app.get("/groups/{group_id}/status")
def get_status(group_id: str):
    res = supabase.table("groups").select("members, finished_members").eq("id", group_id).execute()
    if not res.data:
        return {"error": "Group not found", "is_everyone_done": False}
    
    group = res.data[0]
    members = group.get("members") or []
    finished = group.get("finished_members") or []
    is_done = len(finished) >= len(members) and len(members) > 0

    return {
        "is_everyone_done": is_done,
        "finished_count": len(finished),
        "total_members": len(members)
    }

@app.post("/groups/{group_id}/finish")
def finish_user(group_id: str, payload: FinishPayload):
    user_id = payload.user_id
    res = supabase.table("groups").select("members, finished_members").eq("id", group_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = res.data[0]
    members = group.get("members") or []
    finished = group.get("finished_members") or []

    if user_id not in finished:
        finished.append(user_id)
        supabase.table("groups").update({"finished_members": finished}).eq("id", group_id).execute()

    return {"is_everyone_done": len(finished) >= len(members)}

@app.get("/groups/{group_id}/items")
def get_items(group_id: str):
    try:
        res = supabase.table("restaurants")\
            .select("business_id, name, address, city, stars, categories, photos(image_url)")\
            .limit(1000)\
            .execute()
        
        items_data = res.data
        random.shuffle(items_data)
        selection = items_data[:30]

        translated_items = []
# Inside your loop where you build translated_items:
        for b in selection:
            biz_id = b.get("business_id")
            photo_info = b.get("photos", [])
            db_image = photo_info[0].get("image_url") if photo_info and isinstance(photo_info, list) else None
            
            final_image = db_image if db_image else get_consistent_fallback(biz_id)
            
            # FIX: Handle categories properly
            raw_categories = b.get("categories")

            yelp_style_data = {
                "id": biz_id,
                "name": b.get("name"),
                "rating": b.get("stars"),
                "categories": raw_categories,  # Use the formatted version
                "url": f"https://www.yelp.com/biz/{biz_id}" if biz_id else "#",
                "image_url": final_image,
                "location": {"display_address": [b.get("address"), b.get("city")]}
            }
            translated_items.append(normalize_business(yelp_style_data))

        return {"items": translated_items}
    except Exception as e:
        return {"error": str(e), "items": []}

@app.get("/groups/{group_id}/best")
def best(group_id: str):
    res = supabase.table("ratings").select("*").eq("group_id", group_id).execute()
    ratings = res.data
    if not ratings: return {"error": "no ratings yet"}

    by_item, snap = {}, {}
    for r in ratings:
        item_id = r["item_id"]
        by_item.setdefault(item_id, []).append(r["rating"])
        if item_id not in snap and r.get("item_snapshot"):
            snap[item_id] = r["item_snapshot"]

    best_item_id, best_score = None, float("-inf")
    for item_id, rs in by_item.items():
        score = (0.7 * min(rs)) + (0.3 * (sum(rs)/len(rs))) 
        if score > best_score:
            best_score, best_item_id = score, item_id

    return {"best": {"item": snap.get(best_item_id), "score": best_score}}

@app.get("/groups/{group_id}")
def join_group(group_id: str, user_id: str):
    res = supabase.table("groups").select("members").eq("id", group_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Group not found")

    members = res.data[0]["members"] or []
    if user_id not in members:
        members.append(user_id)
        supabase.table("groups").update({"members": members}).eq("id", group_id).execute()

    return {"group_id": group_id, "members": members}

@app.post("/groups/{group_id}/ratings")
def add_rating(group_id: str, payload: RatingPayload):
    try:
        supabase.table("ratings").insert({
            "group_id": group_id, "user_id": payload.user_id,
            "item_id": payload.item_id, "rating": payload.rating,
            "item_snapshot": payload.item_snapshot,
        }).execute()
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}