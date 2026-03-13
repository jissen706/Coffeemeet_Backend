function Header({ cafeName, description, ownerName }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <span className="header-icon">☕</span>
        <div>
          <div className="cafe-name">{cafeName}</div>
          <div className="cafe-tagline">{description}</div>
        </div>
      </div>
      <div className="header-right">
        <div className="owner-label">Hosted by</div>
        <div className="owner-name">{ownerName}</div>
      </div>
    </header>
  );
}

export default Header;
