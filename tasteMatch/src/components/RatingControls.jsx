export default function RatingControls({ onRate }) {
    return (
      <div className="row">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} onClick={() => onRate(n)} style={{ flex: 1 }}>
            {n}
          </button>
        ))}
      </div>
    );
  }
  