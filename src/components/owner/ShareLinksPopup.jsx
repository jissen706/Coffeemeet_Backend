import { useState } from 'react';

export default function ShareLinksPopup({ cafe, onClose }) {
  const origin = window.location.origin;
  const customerLink = `${origin}/cafe/${cafe.join_code}`;
  const baristaLink  = `${origin}/barista?code=${cafe.join_code}`;

  const [copiedCustomer, setCopiedCustomer] = useState(false);
  const [copiedBarista,  setCopiedBarista]  = useState(false);

  function copy(text, setCopied) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="share-backdrop" onClick={onClose}>
      <div className="share-popup" onClick={e => e.stopPropagation()}>
        <div className="share-header">
          <div className="share-title">Share Your Cafe</div>
          <div className="share-sub">{cafe.name} · Join code: <strong>{cafe.join_code}</strong></div>
        </div>

        <div className="share-links">
          <div className="share-link-block">
            <div className="share-link-label">Customer Link</div>
            <div className="share-link-url">{customerLink}</div>
            <button
              className={`share-copy-btn${copiedCustomer ? ' copied' : ''}`}
              onClick={() => copy(customerLink, setCopiedCustomer)}
            >{copiedCustomer ? '✓ Copied!' : 'Copy'}</button>
          </div>

          <div className="share-link-block">
            <div className="share-link-label">Barista Link</div>
            <div className="share-link-url">{baristaLink}</div>
            <button
              className={`share-copy-btn${copiedBarista ? ' copied' : ''}`}
              onClick={() => copy(baristaLink, setCopiedBarista)}
            >{copiedBarista ? '✓ Copied!' : 'Copy'}</button>
          </div>
        </div>

        <button className="share-dismiss" onClick={onClose}>Done</button>
      </div>
    </div>
  );
}
