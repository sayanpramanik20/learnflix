import React from "react";
import MasteryRing from "./MasteryRing.jsx";

const STATUS_LABEL = {
  struggling: "Struggling",
  developing: "Developing",
  mastered: "Mastered",
};

export default function TopicList({ topics, onExplain }) {
  return (
    <section className="topic-list">
      <h2>Your topics</h2>
      <div className="topic-rows">
        {topics.map((t) => (
          <button
            key={t.topic_id}
            className="topic-row"
            onClick={() => onExplain(t.topic_id)}
            title="Get an AI explanation for this topic"
          >
            <MasteryRing value={t.p_know} status={t.status} size={52} strokeWidth={5} />
            <div className="topic-row-info">
              <span className="topic-row-name">{t.topic_name}</span>
              <span className="topic-row-meta">
                {t.attempts} attempt{t.attempts === 1 ? "" : "s"}
              </span>
            </div>
            <span className={`status-badge status-${t.status}`}>
              {STATUS_LABEL[t.status] || t.status}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
