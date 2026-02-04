import numpy as np
import os
from dotenv import load_dotenv, find_dotenv
import requests
from supabase import create_client 

# Entire Process
# Use yelp to get data about speicfic restraunts and save it then I'll use yelps data to create
# a restraunt dataset, then I'll get my user dataset with their preferences
# then run geometric center to get the average of the users score
# then use that average and cosine simliarirty to find the data closest on the lists of restraunts
#  

#ML Logic Embedding
load_dotenv(find_dotenv())

# API varaiables
#Hugging Face Token and API endpoint
API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
HF_TOKEN = os.getenv("HF_TOKEN")

#SupaBase stuff
supabaseUrl = 'https://rlngfmrwrthxzactluon.supabase.co'
supabaseKey = os.getenv("SUPABASE_KEY")
supabase = create_client(supabaseUrl, supabaseKey)

#Headers for request code
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

#Embedding Function
def embedding(restraunt_preferences):
    #user_vectors = get_embeddings(user_preferences)
    if not API_URL:
        print("Debugging: Missing Credentials")
        return {"error": "API_URL or HF_TOKEN missing"}
    
    response = requests.post(
        API_URL, 
        headers=headers, 
        json={"inputs": restraunt_preferences}
    )

    if response.status_code == 200:
        print("Success! Your Read token is working.")
        print(f"Embedding snippet: {(response.json())[:10]}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        print(f"Error: {response.status_code}")

# Mathematical formulas
# Using geometric center to aggregate all vectors(each users restraunt preferences)
# Centroidsum(vectors) / 6
# The "Democratic" split.Geometric Medianmin(sum(distances))The "Peacekeeper" compromise.
# Medoid min(distance to others)The "Most Relatable" person.
def geometric_center(user_embeddings):
    normalize = 1/len(user_embeddings)
    v_group = np.multiply(normalize, np.sum(user_embeddings))

    return v_group

def geometric_median(user_embeddings):
    pass

def get_mediod(user_embeddings):
    normalize = 1/len(user_embeddings)
    v_group = np.multiply(normalize, np.sum(user_embeddings))

    np.max(v_group)
    pass

# Using geometric center we aggregated all user ratings we can put into cosine_similarity
# formula to get mathetmically closest restraunt to the aggregated user score
def cosine_similarity(v_group, v_res):
    dot_product = np.multiply(v_group, v_res)
    norm = np.multiply(np.linalg.norm(v_group), np.linalg.norm(v_res))

    simliarity = np.divide(dot_product, norm)
    return simliarity

# Quick check script
'''
res = supabase.table("groups").select("*").execute()
print(f"I found {len(res.data)} groups in the cloud!")
for row in res.data:
    print(f"Group ID: {row['id']} | Members: {row['members']}")

print("--- DATABASE CONNECTION DEBUG ---")
print(f"Connecting to: {supabaseUrl}")
# This shows the first 10 letters of your key to confirm which project it is
print(f"Using Key: {supabaseKey[:10] if supabaseKey else 'MISSING!'}...") 
print("---------------------------------")

response = {
     supabase.table("groups").insert({"id": "300", "members": ["Aidan"]}).execute()  
}
print(response)

'''
#Rank Restraunts Function jsut uses other functions I implemented to rank restraunts
# basically embedd then uses the three aggregator functions then performs 
# cosine similarity onto my dataset only problem is I will have to implement supabase function
# basically the restraunt data will be stored on supabased to save storage
def combined(group_id):
    # the code in here should look at which users are in the group and then supabase
    # should have their user preferences and then add every user embedding based on that
    pass

def rank_restraunts(user_preferences):
    user_preference_embedding = np.array(embedding(user_preferences))

    GC_Avg = geometric_center(user_preference_embedding)
    GMedian = geometric_median(user_preference_embedding)
    GMediod = get_mediod(user_preference_embedding)

    # The v res parameter should be our restraunt with all the restraunt embeddings
    restaurant1 = cosine_similarity(GC_Avg, 0)
    restaurant2 = cosine_similarity(GMedian, 0)
    restaurant3 = cosine_similarity(GMediod, 0)


print("------------------------------------\n")
test_user_preference = "I love spicy food but I hate hate salty food. I think salty food is really nasty I hate it so much."
test_user_preference_embedding = np.array(embedding(test_user_preference))
print(test_user_preference_embedding)
print(geometric_center(test_user_preference_embedding))

response = supabase.table("groups").insert({"id": "300", "members": ["Aidan"]}).execute()  
# Temporary test: Comment out the city filter to see if data exists at all
query = supabase.table("businesses").select("*")
# if city:
#    query = query.ilike("city", f"%{city}%")