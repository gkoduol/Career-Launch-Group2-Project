//const API_BASE = "http://127.0.0.1:8000";
const API_BASE = "https://restaurant-swiper-api.onrender.com";

export async function createGroup() {
  const res = await fetch(`${API_BASE}/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic: "restaurants" }),
  });
  return res.json();
}

export async function joinGroup(groupId, userId) {
  const url = new URL(`${API_BASE}/groups/${groupId}`);
  url.searchParams.set("user_id", userId);
  const res = await fetch(url.toString());
  return res.json();
}

export async function fetchItems(groupId, location, term = "restaurants") {
  const url = new URL(`${API_BASE}/groups/${groupId}/items`);
  url.searchParams.set("location", location);
  url.searchParams.set("term", term);
  const res = await fetch(url.toString());
  return res.json();
}

export async function submitRating(groupId, payload) {
  const res = await fetch(`${API_BASE}/groups/${groupId}/ratings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function getBest(groupId) {
  const res = await fetch(`${API_BASE}/groups/${groupId}/best`);
  return res.json();
}

export const finishUser = async (groupId, userId) => {
  const response = await fetch(`${API_BASE}/groups/${groupId}/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }), // Keys must match the Python model exactly
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    console.error("Server validation error:", errorData);
    throw new Error("Validation failed");
  }
  
  return response.json();
};

export const getGroupStatus = async (groupId) => {
  const response = await fetch(`${API_BASE}/groups/${groupId}/status`);
  return response.json();
};