import { useMemo, useState, useEffect } from "react";
import TinderCard from "react-tinder-card";
import "../styles/App.css";
import { createGroup, joinGroup, fetchItems, submitRating, getBest, finishUser, getGroupStatus } from "./services/api";
import { API_URL } from './config'; 

export default function App() {
  const [groupId, setGroupId] = useState("");
  const [userId, setUserId] = useState("user_1");
  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [status, setStatus] = useState("Create or join a group to start.");
  const [isLoading, setIsLoading] = useState(false);
  const [best, setBest] = useState(null);
  const [isGroupFinished, setIsGroupFinished] = useState(false);

  // DEFINE THE LIMIT ONCE
  const CARD_LIMIT = 20;
  const limit = Math.min(cards.length, CARD_LIMIT);
  
  // Only show cards up to the limit
  const current = useMemo(() => {
    return index < limit ? cards[index] : null;
  }, [cards, index, limit]);

  // FIX: Start polling when index reaches limit, not cards.length
  useEffect(() => {
    let interval;
    if (cards.length > 0 && index >= limit && !isGroupFinished && groupId) {
      interval = setInterval(async () => {
        try {
          const data = await getGroupStatus(groupId.trim());
          if (data.is_everyone_done) {
            setIsGroupFinished(true);
            handleBest();
            clearInterval(interval);
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [index, limit, cards.length, isGroupFinished, groupId]); // Added 'limit' to dependencies

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
      const data = await createGroup(userId); 
      const id = (data.group_id || "").toUpperCase();
      if (!id) return setIdle("Backend response missing group_id.");
      setGroupId(id);
      loadRestaurants(id); 
    } catch { setIdle("Create failed."); }
  }

  async function handleJoinGroup() {
    setBest(null);
    if (!groupId.trim()) return setIdle("Enter code first.");
    setBusy("Joining…");
    try {
      const data = await joinGroup(groupId.trim(), userId);
      if (data.error) return setIdle(data.error);
      loadRestaurants(groupId.trim());
    } catch { setIdle("Join failed."); }
  }

  async function loadRestaurants(targetId) {
    setBusy("Loading restaurants…");
    setIndex(0);
    setIsGroupFinished(false); // Reset finished state
    try {
      const data = await fetchItems(targetId || groupId.trim());
      setCards(data.items || []);
      setIdle("");
    } catch { setIdle("Load failed."); }
    finally { setIsLoading(false); }
  }

  async function rate(direction) {
    if (!current) return;
    const ratingValue = direction === 'right' ? 1 : -1;
    const payload = {
      user_id: userId,
      item_id: current.item_id || current.id,
      rating: ratingValue,
      item_snapshot: current,
    };

    const nextIndex = index + 1;
    setIndex(nextIndex);

    try {
      await submitRating(groupId.trim(), payload);
      
      // FIX: Use the consistent limit
      if (nextIndex >= limit) {
        setTimeout(() => {
          handleUserFinished();
        }, 700);
      }
    } catch (e) { console.error("Save failed", e); }
  }

  async function handleUserFinished() {
    setBusy("Building your taste profile...");
    
    // Build user preference vector from their likes
    try {
      await fetch(`${API_URL}/groups/${groupId.trim()}/user-vector`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
    } catch (e) {
      console.error("Vector building failed", e);
    }
    
    setBusy("Waiting for group...");
    try {
      const data = await finishUser(groupId.trim(), userId);
      if (data.is_everyone_done) {
        setIsGroupFinished(true);
        handleBest();
      }
    } catch (e) { 
      console.error("Finish call failed", e); 
    }
  }

  async function handleBest() {
    setBest(null);
    setBusy("Finding best match with ML...");
    try {
      // Call the ML endpoint instead of the old one
      const response = await fetch(`${API_URL}/groups/${groupId.trim()}/best-ml`);
      const data = await response.json();
      
      setBest(data.best?.item || null);
    } catch (error) {
      console.error("Match failed", error);
      setIdle("Match failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div className="titleBlock">
          <h1>TasteMatch</h1>
        </div>
        {groupId && <div className="groupPill">Group: {groupId}</div>}
      </header>

      {cards.length === 0 && (
        <section className="panel">
          <div className="controls">
            <div className="formGrid">
              <input placeholder="GROUP CODE" value={groupId} onChange={(e) => setGroupId(e.target.value.toUpperCase())} />
              <input placeholder="YOUR NAME" value={userId} onChange={(e) => setUserId(e.target.value)} />
            </div>
            <div className="buttonRow">
              <button onClick={handleCreateGroup} disabled={isLoading}>New Group</button>
              <button onClick={handleJoinGroup} disabled={!groupId || isLoading}>Join Group</button>
            </div>
            <div className="status">{status}</div>
          </div>
        </section>
      )}

      <section className="main">
        <div className="card-container">
          {current ? (
              <TinderCard key={current.item_id || current.id} onSwipe={rate} preventSwipe={["up", "down"]}>
                <div className="card">
                  <img src={current.image_url} alt={current.name} />
                  <div className="content">
                    <h2>{current.name}</h2>
                    <div className="category-pill">{current.categories}</div>
                    <p className="details">⭐ {current.rating || "—"} • {current.address}</p>
                    
                    {/* ADD THIS: */}
                    {current.url && current.url !== "#" && (
                      <a 
                        href={current.url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="yelp-link"
                        onClick={(e) => e.stopPropagation()} // Prevent triggering swipe
                      >
                        View on Yelp ↗
                      </a>
                    )}
                  </div>
                </div>
              </TinderCard>
          ) : cards.length > 0 ? (
            <div className="done-screen">
               {isGroupFinished ? (
                  <div className="finished-celebration">
                    <p>🎉 Match Found!</p>
                    <button className="primaryBtn" onClick={handleBest}>View Winner</button>
                  </div>
               ) : (
                  <div className="waiting-vibe">
                    <div className="loader"></div>
                    <p>Waiting for the rest of the group...</p>
                  </div>
               )}
            </div>
          ) : null}
        </div>

        {current && (
          <div className="rating-buttons">
            <button className="dislike-btn" onClick={() => rate('left')}>✖</button>
            <button className="like-btn" onClick={() => rate('right')}>❤️</button>
          </div>
        )}
      </section>

      {best && (
        <div className="modalBackdrop" onClick={() => setBest(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-content">
              <span className="winner-tag">🏆 THE WINNER IS</span>
              <img src={best.image_url} alt={best.name} className="winner-image" />
              <h2>{best.name}</h2>
              <p className="category">{best.categories || "Restaurant"}</p>
              <p className="address">{best.address}</p>
              
              <div className="modal-actions">
                {best.url && (
                  <a href={best.url} target="_blank" rel="noopener noreferrer" className="primaryBtn">
                    View on Yelp ↗
                  </a>
                )}
                <button className="secondaryBtn" onClick={() => setBest(null)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}