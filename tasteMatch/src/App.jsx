import { useMemo, useState } from "react";
import { getStableUserId } from "./utils/userId";
import { mockRestaurants } from "./data/mockRestaurants";

import GroupSetup from "./components/GroupSetup";
import LocationSearch from "./components/LocationSearch";
import RestaurantCard from "./components/RestaurantCard";
import RatingControls from "./components/RatingControls";
import Results from "./components/Results";

export default function App() {
  const userId = useMemo(() => getStableUserId(), []);

  const [step, setStep] = useState("group"); // group -> location -> rate -> results
  const [groupId, setGroupId] = useState("");
  const [joinInput, setJoinInput] = useState("");

  const [location, setLocation] = useState("");
  const [restaurants, setRestaurants] = useState([]);
  const [idx, setIdx] = useState(0);

  const [ratings, setRatings] = useState([]);

  // MOCK: create group just makes a code
  function createGroup() {
    const code = Math.random().toString(36).substring(2, 8).toUpperCase();
    setGroupId(code);
    setJoinInput(code);
  }

  // MOCK: join group just accepts whatever was typed
  function joinGroup(code) {
    if (!code.trim()) return;
    setGroupId(code.trim().toUpperCase());
    setStep("location");
  }

  // MOCK: load restaurants just loads local data
  function loadRestaurants() {
    if (!groupId) return;
    if (!location.trim()) return;
    setRestaurants(mockRestaurants);
    setIdx(0);
    setStep("rate");
  }

  // MOCK: rating sends JSON locally (later this becomes a fetch POST)
  function rateRestaurant(value) {
    const current = restaurants[idx];
    if (!current) return;

    const payload = {
      user_id: userId,
      group_id: groupId,
      item_id: current.item_id,
      rating: value
    };

    setRatings((prev) => [...prev, payload]);

    const next = idx + 1;
    if (next >= restaurants.length) {
      setStep("results");
    } else {
      setIdx(next);
    }
  }

  function restart() {
    setStep("group");
    setGroupId("");
    setJoinInput("");
    setLocation("");
    setRestaurants([]);
    setIdx(0);
    setRatings([]);
  }

  return (
    <div className="container">
      <h1>TasteMatch</h1>

      {step === "group" && (
        <GroupSetup
          groupId={groupId}
          joinInput={joinInput}
          setJoinInput={setJoinInput}
          onCreateGroup={createGroup}
          onJoinGroup={joinGroup}
        />
      )}

      {step === "location" && (
        <LocationSearch
          location={location}
          setLocation={setLocation}
          onLoad={loadRestaurants}
        />
      )}

      {step === "rate" && restaurants[idx] && (
        <>
          <RestaurantCard r={restaurants[idx]} index={idx} total={restaurants.length} />
          <RatingControls onRate={rateRestaurant} />
        </>
      )}

      {step === "results" && (
        <Results ratings={ratings} onRestart={restart} />
      )}

      <div className="footer">Data provided by Yelp (once backend is connected).</div>
    </div>
  );
}
