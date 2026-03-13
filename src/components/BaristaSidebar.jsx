function BaristaSidebar({ baristas }) {
  return (
    <aside className="barista-sidebar">
      <div className="sidebar-title">Baristas</div>

      {baristas.length === 0 ? (
        <div className="no-baristas">
          <span>No baristas registered yet.</span>
        </div>
      ) : (
        baristas.map((barista) => {
          const initials = barista.name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .slice(0, 2)
            .toUpperCase();

          return (
            <div key={barista.id} className="barista-card">
              <div className="barista-card-top">
                <div className="barista-avatar">{initials}</div>
                <div className="barista-name">{barista.name}</div>
              </div>
              <div className="barista-expertise">
                <span>&#9749;</span> {barista.expertise}
              </div>
              <div className="barista-contact">
                <div className="barista-contact-row">
                  <span className="contact-icon">&#9993;</span>
                  <span>{barista.email}</span>
                </div>
                {barista.phone_number && (
                  <div className="barista-contact-row">
                    <span className="contact-icon">&#128222;</span>
                    <span>{barista.phone_number}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
    </aside>
  );
}

export default BaristaSidebar;
