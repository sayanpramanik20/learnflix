import React from "react";

const FORMAT_LABEL = {
  video: "Video walkthrough",
  text: "Analogy explainer",
  practice: "Practice drill",
};

export default function RecommendedHero({ recommendation, message, busy, onStartQuiz, onExplain }) {
  if (message) {
    return (
      <section className="hero hero-empty">
        <span className="eyebrow">Recommended for you</span>
        <p>{message}</p>
      </section>
    );
  }

  if (!recommendation) {
    return (
      <section className="hero hero-empty">
        <span className="eyebrow">Recommended for you</span>
        <p>Loading your next lesson...</p>
      </section>
    );
  }

  const { title, format, topic_name, reason, mastery_gap } = recommendation;

  return (
    <section className="hero">
      <span className="eyebrow">Recommended for you</span>
      <div className="hero-body">
        <div className="hero-format-badge" data-format={format}>
          {FORMAT_LABEL[format] || format}
        </div>
        <h1>{title}</h1>
        <p className="hero-topic">{topic_name}</p>
        <p className="hero-reason">{reason}</p>

        <div className="hero-actions">
          <button
            className="btn btn-primary"
            disabled={busy}
            onClick={onStartQuiz}
          >
            Take a micro-quiz
          </button>
          <button className="btn btn-ghost" disabled={busy} onClick={() => onExplain(recommendation.topic_id, format)}>Explain this to me</button>
        </div>

        <p className="hero-gap">
          Mastery gap to target: <span className="mono">{Math.round(mastery_gap * 100)}%</span>
        </p>
      </div>
    </section>
  );
}
