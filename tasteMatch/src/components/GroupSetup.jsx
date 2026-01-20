export default function GroupSetup({
    groupId,
    joinInput,
    setJoinInput,
    onCreateGroup,
    onJoinGroup
  }) {
    return (
      <div className="panel">
        <div className="panelHead">
          <h2>Step 1: Create or Join a Group</h2>
          <div className="sub">
            Share the group code with friends so everyone rates the same restaurants.
          </div>
        </div>
  
        <div className="panelBody">
          <div className="stack">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <button className="btnPrimary" onClick={onCreateGroup}>
                Create Group
              </button>
              {groupId ? <div className="pill">Group Code: <strong>{groupId}</strong></div> : <div className="pill">No group yet</div>}
            </div>
  
            <div className="hr" />
  
            <div className="stack">
              <div className="muted" style={{ fontSize: 13 }}>
                Already have a code?
              </div>
  
              <div className="row">
                <input
                  value={joinInput}
                  onChange={(e) => setJoinInput(e.target.value)}
                  placeholder="Enter group code (ex: A1B2C3)"
                />
                <button onClick={() => onJoinGroup(joinInput)}>Join</button>
              </div>
  
              <div className="muted" style={{ fontSize: 12, lineHeight: 1.35 }}>
                Tip: Keep codes short and easy to read (all caps helps).
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  