export default function Results({ ratings, onRestart }) {
    return (
      <div className="card">
        <h2>Step 4: Results (Mock)</h2>
        <p className="muted">
          Backend isn’t connected yet — this is just showing the ratings you submitted locally.
        </p>
  
        <pre className="pre">{JSON.stringify(ratings, null, 2)}</pre>
  
        <button onClick={onRestart}>Restart</button>
      </div>
    );
  }
  