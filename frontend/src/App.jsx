import { useMemo, useState } from "react";
import TinderCard from "react-tinder-card";
import "../styles/App.css";
import { createGroup, joinGroup, fetchItems, submitRating, getBest } from "./services/api";

export default function App() {
  const [groupId, setGroupId] = useState("");
  const [userId, setUserId] = useState("user_1");

  const [location, setLocation] = useState("");
  const [term, setTerm] = useState("restaurants");

  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);

  const [status, setStatus] = useState("Create or join a group to start.");
  const [isLoading, setIsLoading] = useState(false);

  const [best, setBest] = useState(null);

  const current = useMemo(() => cards[index], [cards, index]);

  function setBusy(message) {
    setIsLoading(true);
    setStatus(message);
  }
  function setIdle(message) {
    setIsLoading(false);
    setStatus(message);
  }

  async function handleCreateGroup() {
    setBest(null);
    setBusy("Creating group…");
    try {
      const data = await createGroup();
      const id = (data.group_id || data.groupId || "").toUpperCase();
      if (!id) return setIdle("Backend response missing group_id.");
      setGroupId(id);
      setIdle(`Created group ${id}. Share this code with friends.`);
    } catch {
      setIdle("Create group failed. Check backend / CORS.");
    }
  }

  async function handleJoinGroup() {
    setBest(null);
    if (!groupId.trim()) return setIdle("Enter a group code first.");
    setBusy("Joining group…");
    try {
      const data = await joinGroup(groupId.trim(), userId);
      if (data.error) return setIdle(data.error);
      setIdle(`Joined ${groupId.trim()} as ${userId}.`);
    } catch {
      setIdle("Join failed. Check backend / CORS.");
    }
  }

  async function loadRestaurants() {
    setBest(null);
    if (!groupId.trim()) return setIdle("Enter a group code first.");
    if (!location.trim()) return setIdle("Enter a location first.");

    setBusy("Loading restaurants…");
    setIndex(0);

    try {
      const data = await fetchItems(
        groupId.trim(),
        location.trim(),
        term.trim() || "restaurants"
      );
      if (data.error) return setIdle(data.error);

      const items = data.items || [];
      setCards(items);
      setIdle(
        items.length
          ? `Loaded ${items.length} places. Start rating!`
          : "No results found for that search."
      );
    } catch {
      setIdle("Load failed. Check backend / CORS.");
    } finally {
      setIsLoading(false);
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

    setBusy(`Sending rating ${rating}…`);
    try {
      const res = await submitRating(groupId.trim(), payload);
      if (res?.error) setIdle(res.error);
      else setIdle(`Rated ${current.name}: ${rating}/5`);
    } catch {
      setIdle("Rating send failed. Check backend / CORS.");
    } finally {
      setIndex((i) => i + 1);
      setIsLoading(false);
    }
  }

  async function handleBest() {
    setBest(null);
    if (!groupId.trim()) return setIdle("Enter a group code first.");
    setBusy("Finding best match…");
    try {
      const data = await getBest(groupId.trim());
      if (data.error) return setIdle(data.error);

      setBest(data.best?.item || null);
      setIdle("Best match selected!");
    } catch {
      setIdle("Best match failed. Check backend / CORS.");
    } finally {
      setIsLoading(false);
    }
  }

  const canJoin = !!groupId.trim() && !!userId.trim();
  const canLoad = !!groupId.trim() && !!location.trim();

  return (
    <div className="page">
      <header className="header">
        <div className="titleBlock">
          <h1>Restaurant Swipe</h1>
          <p>Rate options individually, then compute the best match for the group.</p>
        </div>

        {groupId.trim() ? (
          <div className="groupPill">Group: {groupId.trim()}</div>
        ) : null}
      </header>

      <section className="panel">
        <div className="controls">
          <div className="buttonRow">
            <button onClick={handleCreateGroup} disabled={isLoading}>
              Create Group
            </button>
            <button onClick={handleJoinGroup} disabled={!canJoin || isLoading}>
              Join Group
            </button>
          </div>

          <div className="formGrid">
            <input
              placeholder="Group Code (e.g. ABCD12)"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value.toUpperCase())}
            />

            <input
              placeholder="User ID (e.g. user_1)"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            />

            <input
              className="full"
              placeholder="Location (City, State or ZIP)"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />

            <input
              className="full"
              placeholder="What are you craving? (thai, sushi, pizza...)"
              value={term}
              onChange={(e) => setTerm(e.target.value)}
            />
          </div>

          <button
            className="primaryBtn"
            onClick={loadRestaurants}
            disabled={!canLoad || isLoading}
          >
            {isLoading ? "Loading…" : "Load Restaurants"}
          </button>

          <div className="status">{status}</div>
        </div>
      </section>

      <section className="main">
        <div className="card-container">
          {current ? (
            <TinderCard
              key={current.item_id || current.id}
              preventSwipe={["up", "down"]}
            >
              <div className="card">
                {current.image_url ? (
                  <img src={current.image_url} alt={current.name} />
                ) : null}

                <div className="content">
                  <h2>{current.name}</h2>

                  <p>
                    ⭐ {current.rating ?? "—"}{" "}
                    {current.review_count ? `(${current.review_count})` : ""}{" "}
                    {current.price ? `· ${current.price}` : ""}
                  </p>

                  {current.address ? (
                    <p className="address">{current.address}</p>
                  ) : null}

                  {current.url ? (
                    <a
                      className="link"
                      href={current.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      View on Yelp →
                    </a>
                  ) : null}
                </div>
              </div>
            </TinderCard>
          ) : (
            <p className="done">
              {cards.length ? "No more restaurants." : "Load restaurants to start."}
            </p>
          )}
        </div>

        {current ? (
          <div className="rating-buttons">
            {[1, 2, 3, 4, 5].map((r) => (
              <button key={r} onClick={() => rate(r)} disabled={isLoading}>
                {r}
              </button>
            ))}
            <button className="bestBtn" onClick={handleBest} disabled={isLoading}>
              Get Best Match
            </button>
          </div>
        ) : null}
      </section>

      {best ? (
        <div
          className="modalBackdrop"
          onClick={() => setBest(null)}
          role="button"
          tabIndex={0}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="content">
              <h2 style={{ marginTop: 0 }}>Best Match</h2>
              <p style={{ marginTop: 6 }}>
                {best.name ? best.name : "Best match selected (no snapshot available)."}
              </p>
              {best.url ? (
                <a className="link" href={best.url} target="_blank" rel="noreferrer">
                  View on Yelp →
                </a>
              ) : null}

              <div style={{ marginTop: 14 }}>
                <button className="primaryBtn" onClick={() => setBest(null)}>
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}