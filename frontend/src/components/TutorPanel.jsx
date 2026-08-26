import React from "react";

const STYLES = [
  { id: "video", label: "Video script" },
  { id: "text", label: "Analogy" },
  { id: "practice", label: "Practice" },
];

export default function TutorPanel({ open, onClose, topicName, loading, explanation, styleUsed, onPickStyle }) {
  return (
    <aside className={`tutor-panel ${open ? "tutor-panel-open" : ""}`} aria-hidden={!open}>
      <div className="tutor-panel-header">
        <div>
          <span className="eyebrow">Learnflix</span>
          <h3>{topicName}</h3>
        </div>
        <button className="tutor-panel-close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>

      <div className="tutor-panel-styles">
        {STYLES.map((s) => (
          <button
            key={s.id}
            className={`style-chip ${styleUsed === s.id ? "style-chip-active" : ""}`}
            onClick={() => onPickStyle(s.id)}
            disabled={loading}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="tutor-panel-body">
        {loading ? (
          <p className="tutor-panel-loading">Generating a personalised explanation…</p>
        ) : (
          <p className="tutor-panel-text">{explanation}</p>
        )}
      </div>
    </aside>
  );
}
