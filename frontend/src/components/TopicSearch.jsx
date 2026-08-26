import React, { useState } from "react";
import { api } from "../api.js";

export default function TopicSearch({ grade }) {
  const [query, setQuery] = useState("");
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function search(nextQuery = query) {
    const value = nextQuery.trim();
    if (value.length < 2) return;
    setQuery(value);
    setLoading(true);
    setError(null);
    try {
      setLesson(await api.searchTopic(value, grade));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function submit(event) {
    event.preventDefault();
    search();
  }

  return (
    <section className="topic-search">
      <div className="search-intro">
        <span className="eyebrow">Explore the open web</span>
        <h1>What are you curious about?</h1>
        <p>Gemini searches current sources, then turns them into a lesson at your level.</p>
      </div>
      <form className="search-form" onSubmit={submit}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try: black holes, photosynthesis, blockchain..." aria-label="Search a topic" />
        <button className="btn btn-primary" disabled={loading || query.trim().length < 2}>{loading ? "Searching..." : "Learn"}</button>
      </form>
      {error && <div className="banner banner-error">{error}</div>}
      {lesson && (
        <article className="lesson-result">
          <div className="lesson-result-header">
            <div>
              <span className={`search-status ${lesson.grounded ? "search-status-grounded" : "search-status-fallback"}`}>{lesson.grounded ? "Web-grounded lesson" : "Offline lesson"}</span>
              <h2>{lesson.title}</h2>
            </div>
            <span className="mono">{lesson.query}</span>
          </div>
          <p className="lesson-summary">{lesson.summary}</p>
          <div className="lesson-columns">
            <div>
              <h3>Key ideas</h3>
              <ul className="lesson-points">{lesson.key_points.map((point) => <li key={point}>{point}</li>)}</ul>
            </div>
            <div>
              <h3>Study next</h3>
              <div className="recommended-topics">{lesson.recommended_topics.map((topic) => <button key={topic} onClick={() => search(topic)}>{topic}<span>→</span></button>)}</div>
            </div>
          </div>
          {lesson.sources.length > 0 && <div className="lesson-sources"><h3>Sources</h3>{lesson.sources.map((source) => <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>{source.title || source.url}<span>↗</span></a>)}</div>}
        </article>
      )}
    </section>
  );
}
