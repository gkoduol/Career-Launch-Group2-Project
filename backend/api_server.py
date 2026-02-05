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
import numpy as np

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
        # Fetch MORE than we need (100 instead of 30)
        res = supabase.table("restaurants")\
            .select("business_id, name, address, city, stars, categories")\
            .limit(10000)\
            .execute()
        
        items_data = res.data
        random.shuffle(items_data)
        
        translated_items = []
        
        # Keep going until we have 30 restaurants with valid images
        for b in items_data:
            if len(translated_items) >= 30:
                break  # We have enough!
            
            biz_id = b.get("business_id")
            
            # Try to get photo from photos table
            photo_res = supabase.table("photos")\
                .select("*")\
                .eq("business_id", biz_id)\
                .limit(1)\
                .execute()
            
            image_url = None
            
            if photo_res.data:
                photo = photo_res.data[0]
                # Try different field names
                image_url = (
                    photo.get("image_url") or 
                    photo.get("photo_url") or 
                    photo.get("url")
                )
                
                # Construct from photo_id if exists
                if not image_url and photo.get("photo_id"):
                    photo_id = photo.get("photo_id")
                    image_url = f"https://s3-media0.fl.yelpcdn.com/bphoto/{photo_id}/o.jpg"
            
            # SKIP this restaurant if no valid image found
            if not image_url:
                logger.info(f"Skipping {b.get('name')} - no valid image")
                continue
            
            # Only add restaurants with valid images
            raw_categories = b.get("categories")

            yelp_style_data = {
                "id": biz_id,
                "name": b.get("name"),
                "rating": b.get("stars"),
                "categories": raw_categories,
                "url": f"https://www.yelp.com/biz/{biz_id}" if biz_id else "#",
                "image_url": image_url,
                "location": {"display_address": [b.get("address"), b.get("city")]}
            }
            translated_items.append(normalize_business(yelp_style_data))
        
        logger.info(f"Selected {len(translated_items)} restaurants with valid images")
        
        return {"items": translated_items}
        
    except Exception as e:
        logger.error(f"Error in get_items: {e}")
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
    
@app.post("/groups/{group_id}/user-vector")
def build_user_vector(group_id: str, payload: Dict[str, Any]):
    """Build user preference vector from their liked restaurants"""
    try:
        user_id = payload.get("user_id")
        logger.info(f"Building vector for user {user_id} in group {group_id}")
        
        # Get all restaurants this user liked (rating = 1)
        ratings_res = supabase.table("ratings")\
            .select("item_id")\
            .eq("group_id", group_id)\
            .eq("user_id", user_id)\
            .eq("rating", 1)\
            .execute()
        
        liked_items = [r["item_id"] for r in ratings_res.data]
        logger.info(f"User liked {len(liked_items)} items")
        
        if not liked_items:
            return {"error": "No liked items", "liked_count": 0}
        
        # Fetch embeddings for all liked restaurants
        embeddings = []
        for item_id in liked_items:
            rest_res = supabase.table("restaurants")\
                .select("embedding")\
                .eq("business_id", item_id)\
                .execute()
            
            if rest_res.data and rest_res.data[0].get("embedding"):
                raw_embedding = rest_res.data[0]["embedding"]
                
                # PARSE: Convert string to actual array
                if isinstance(raw_embedding, str):
                    # Remove brackets and parse
                    import json
                    embedding_array = json.loads(raw_embedding)
                elif isinstance(raw_embedding, list):
                    embedding_array = raw_embedding
                else:
                    logger.warning(f"Unknown embedding type: {type(raw_embedding)}")
                    continue
                
                embeddings.append(embedding_array)
        
        logger.info(f"Found {len(embeddings)} embeddings")
        
        if not embeddings:
            return {"error": "No embeddings found for liked items"}
        
        # Convert to numpy array first, then calculate mean
        embeddings_array = np.array(embeddings, dtype=np.float32)
        user_vector = np.mean(embeddings_array, axis=0).tolist()
        
        logger.info(f"Created user vector with {len(user_vector)} dimensions")
        
        # Store user vector (as list, will be converted to vector by pgvector)
        supabase.table("user_vectors").upsert({
            "group_id": group_id,
            "user_id": user_id,
            "preference_vector": user_vector
        }, on_conflict="group_id,user_id").execute()
        
        logger.info("Successfully stored user vector")
        
        return {
            "ok": True,
            "vector_dims": len(user_vector),
            "liked_count": len(liked_items)
        }
        
    except Exception as e:
        logger.error(f"ERROR in build_user_vector: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/groups/{group_id}/best-ml")
def best_ml(group_id: str):
    """Find best restaurant using vector similarity"""
    
    try:
        # Get all user preference vectors for this group
        vectors_res = supabase.table("user_vectors")\
            .select("preference_vector")\
            .eq("group_id", group_id)\
            .execute()
        
        if not vectors_res.data:
            logger.warning("No user vectors found, using fallback method")
            return best(group_id)
        
        # Parse and aggregate user vectors
        user_vectors = []
        for r in vectors_res.data:
            raw_vector = r["preference_vector"]
            
            # Parse if string
            if isinstance(raw_vector, str):
                import json
                vector_array = json.loads(raw_vector)
            elif isinstance(raw_vector, list):
                vector_array = raw_vector
            else:
                continue
            
            user_vectors.append(vector_array)
        
        if not user_vectors:
            return best(group_id)
        
        # Average all user preference vectors
        group_vector_array = np.array(user_vectors, dtype=np.float32)
        group_vector = np.mean(group_vector_array, axis=0).tolist()
        
        # Get items already rated by the group
        ratings_res = supabase.table("ratings")\
            .select("item_id")\
            .eq("group_id", group_id)\
            .execute()
        rated_items = {r["item_id"] for r in ratings_res.data}
        
        # Use pgvector to find most similar restaurants
        result = supabase.rpc(
            'match_restaurants',
            {
                'query_embedding': group_vector,
                'match_threshold': 0.0,
                'match_count': 50
            }
        ).execute()
        
        # Find first non-rated restaurant
        best_restaurant = None
        for restaurant in result.data:
            if restaurant["business_id"] not in rated_items:
                best_restaurant = restaurant
                break
        
        if not best_restaurant:
            return {"error": "No suitable restaurant found"}
        
        # Fetch photo - multi-step approach
        final_image = None
        
        # Step 1: Try database
        try:
            photo_res = supabase.table("photos")\
                .select("*")\
                .eq("business_id", best_restaurant["business_id"])\
                .limit(1)\
                .execute()
            
            if photo_res.data:
                photo = photo_res.data[0]
                # Try different field names
                final_image = (
                    photo.get("image_url") or 
                    photo.get("photo_url") or 
                    photo.get("url")
                )
                
                # If photo_id exists, construct Yelp CDN URL
                if not final_image and photo.get("photo_id"):
                    photo_id = photo.get("photo_id")
                    final_image = f"https://s3-media0.fl.yelpcdn.com/bphoto/{photo_id}/o.jpg"
        except Exception as e:
            logger.warning(f"Database photo fetch failed: {e}")
        
        # Step 2: Try scraped_image column (if you added it)
        if not final_image:
            try:
                rest_res = supabase.table("restaurants")\
                    .select("scraped_image")\
                    .eq("business_id", best_restaurant["business_id"])\
                    .execute()
                
                if rest_res.data and rest_res.data[0].get("scraped_image"):
                    final_image = rest_res.data[0]["scraped_image"]
            except:
                pass
        
        # Step 4: Fallback to consistent default
        if not final_image:
            logger.warning(f"No image found for {best_restaurant['business_id']}, using fallback")
            final_image = get_consistent_fallback(best_restaurant["business_id"])
        
        return {
            "best": {
                "item": {
                    "item_id": best_restaurant["business_id"],
                    "name": best_restaurant["name"],
                    "rating": best_restaurant["stars"],
                    "categories": best_restaurant["categories"],
                    "address": best_restaurant["address"],
                    "image_url": final_image,
                    "url": f"https://www.yelp.com/biz/{best_restaurant['business_id']}"
                },
                "score": float(best_restaurant["similarity"]),
                "method": "ml_vector_similarity"
            }
        }
        
    except Exception as e:
        logger.error(f"ML matching error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Fallback to old method
        return best(group_id)
