import { useMemo, useState } from "react";
import TinderCard from "react-tinder-card";
import "./App.css";
import { createGroup, joinGroup, fetchItems, submitRating, getBest } from "./api";

export default function App() {
  const [groupId, setGroupId] = useState("");
  const [userId, setUserId] = useState("user_1");

  const [location, setLocation] = useState("");
  const [term, setTerm] = useState("restaurants");

  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [status, setStatus] = useState("Create or join a group to start.");

  const current = useMemo(() => cards[index], [cards, index]);

  async function handleCreateGroup() {
    setStatus("Creating group...");
    try {
      const data = await createGroup();
      const id = (data.group_id || data.groupId || "").toUpperCase();
      if (!id) return setStatus("Backend response missing group_id.");
      setGroupId(id);
      setStatus(`Created group: ${id}`);
    } catch {
      setStatus("Create group failed (backend not live yet).");
    }
  }

  async function handleJoinGroup() {
    if (!groupId.trim()) return setStatus("Enter a group code first.");
    setStatus("Joining group...");
    try {
      const data = await joinGroup(groupId.trim(), userId);
      if (data.error) return setStatus(data.error);
      setStatus(`Joined ${groupId.trim()} as ${userId}`);
    } catch {
      setStatus("Join failed (backend not live yet).");
    }
  }

  async function loadRestaurants() {
    if (!groupId.trim()) return setStatus("Enter a group code first.");
    if (!location.trim()) return setStatus("Enter a location first.");

    setStatus("Loading restaurants...");
    setIndex(0);
    try {
      const data = await fetchItems(groupId.trim(), location.trim(), term.trim() || "restaurants");
      if (data.error) return setStatus(data.error);

      setCards(data.items || []);
      setStatus(`Loaded ${(data.items || []).length} restaurants`);
    } catch {
      setStatus("Load failed (backend not live yet).");
    }
  }

  async function rate(rating) {
    if (!current) return;

    const payload = {
      user_id: userId,
      item_id: current.item_id || current.id,
      rating,
      item_snapshot: current,
    };

    setStatus(`Sending rating ${rating}...`);

    try {
      const res = await submitRating(groupId.trim(), payload);
      if (res?.error) setStatus(res.error);
      else setStatus(`Rated ${current.name}: ${rating}`);
    } catch {
      setStatus("Rating send failed (backend not live yet).");
    }

    setIndex((i) => i + 1);
  }

  async function handleBest() {
    if (!groupId.trim()) return setStatus("Enter a group code first.");
    setStatus("Getting best match...");
    try {
      const data = await getBest(groupId.trim());
      if (data.error) return setStatus(data.error);
      setStatus(`Best match ready. (Backend returned: ${data.best?.item?.name || "ok"})`);
    } catch {
      setStatus("Best match failed (backend not live yet).");
    }
  }

  return (
    <div className="page">
      <h1>🍽️ Restaurant Swipe</h1>

      <div className="controls">
        <div className="buttonRow">
          <button onClick={handleCreateGroup}>Create Group</button>
          <button onClick={handleJoinGroup}>Join Group</button>
        </div>

        <input
          placeholder="Group Code (e.g. ABCD12)"
          value={groupId}
          onChange={(e) => setGroupId(e.target.value.toUpperCase())}
        />
        <input placeholder="User ID" value={userId} onChange={(e) => setUserId(e.target.value)} />
        <input
          placeholder="Location (City, State or ZIP)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <input
          placeholder="What are you craving? (thai, sushi, pizza...)"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />

        <button onClick={loadRestaurants}>Load Restaurants</button>
      </div>

      <div className="status">{status}</div>

      <div className="card-container">
        {current ? (
          <TinderCard key={current.item_id || current.id} preventSwipe={["up", "down"]}>
            <div className="card">
              {current.image_url && <img src={current.image_url} alt={current.name} />}
              <h2>{current.name}</h2>
              <p>
                ⭐ {current.rating ?? "—"} {current.review_count ? `(${current.review_count})` : ""}{" "}
                {current.price ? `· ${current.price}` : ""}
              </p>
              <p className="address">{current.address || ""}</p>
              {current.url && (
                <a className="link" href={current.url} target="_blank" rel="noreferrer">
                  Open listing
                </a>
              )}
            </div>
          </TinderCard>
        ) : (
          <p className="done">{cards.length ? "No more restaurants." : "Load restaurants to start."}</p>
        )}
      </div>

      {current && (
        <div className="rating-buttons">
          {[1, 2, 3, 4, 5].map((r) => (
            <button key={r} onClick={() => rate(r)}>
              {r}
            </button>
          ))}
          <button className="bestBtn" onClick={handleBest}>
            Get Best
          </button>
        </div>
      )}
    </div>
  );
}