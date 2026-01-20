export default function RestaurantCard({ r, index, total }) {
    return (
      <div className="card">
        {r.image_url && <img className="img" src={r.image_url} alt={r.name} />}
  
        <div className="cardInner">
          <div className="muted" style={{ fontSize: 13 }}>
            Restaurant {index + 1} / {total}
          </div>
  
          <h2 style={{ margin: "10px 0 6px", fontSize: 22, letterSpacing: "-0.3px" }}>
            {r.name}
          </h2>
  
          <div className="muted" style={{ lineHeight: 1.35 }}>
            {r.address || "Address unavailable"}
          </div>
  
          <div className="tagRow">
            {r.price && <span className="tag">{r.price}</span>}
            {typeof r.rating === "number" && <span className="tag">Yelp {r.rating}⭐</span>}
            {typeof r.review_count === "number" && (
              <span className="tag">{r.review_count} reviews</span>
            )}
          </div>
  
          {r.url && (
            <div style={{ marginTop: 12 }}>
              <a href={r.url} target="_blank" rel="noreferrer">
                View on Yelp →
              </a>
            </div>
          )}
        </div>
      </div>
    );
  }
  