export default function LocationSearch({ location, setLocation, onLoad }) {
    return (
      <div className="panel">
        <div className="panelHead">
          <h2>Step 2: Enter Location</h2>
          <div className="sub">
            Choose a city / area to pull restaurants (mock data for now).
          </div>
        </div>
  
        <div className="panelBody">
          <div className="stack">
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Ex: College Park, MD"
            />
            <button className="btnPrimary" onClick={onLoad}>
              Load Restaurants
            </button>
          </div>
        </div>
      </div>
    );
  }
  