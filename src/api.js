const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

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