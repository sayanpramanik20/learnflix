import React from "react";

function TrendLine({ points }) {
  if (!points.length) return <span className="trend-empty">No attempts yet</span>;
  const width = 180;
  const height = 54;
  const values = points.map((point) => point.p_know);
  const min = Math.max(0, Math.min(...values) - 0.08);
  const max = Math.min(1, Math.max(...values) + 0.08);
  const range = max - min || 1;
  const path = points.map((point, index) => {
    const x = (index / Math.max(points.length - 1, 1)) * width;
    const y = height - ((point.p_know - min) / range) * height;
    return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return <svg className="trend-line" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Mastery trend"><path d={path} /></svg>;
}

export default function AnalyticsDashboard({ analytics, classAnalytics, students, selectedStudentId, onStudentChange }) {
  if (!analytics || !classAnalytics) return <div className="empty-state">Loading classroom analytics...</div>;
  return (
    <main className="analytics-main">
      <div className="analytics-heading">
        <div>
          <span className="eyebrow">Teacher view / live classroom signal</span>
          <h1>Learning pulse</h1>
        </div>
        <label className="analytics-student-select">
          <span>Inspect learner</span>
          <select value={selectedStudentId} onChange={(event) => onStudentChange(Number(event.target.value))}>
            {students.map((student) => <option key={student.id} value={student.id}>{student.name}</option>)}
          </select>
        </label>
      </div>
      <section className="analytics-kpis">
        <div className="analytics-kpi"><span>Class mastery</span><strong>{Math.round(classAnalytics.avg_overall_mastery * 100)}%</strong><small>Across {classAnalytics.total_students} learners</small></div>
        <div className="analytics-kpi"><span>Active in 24 hours</span><strong>{classAnalytics.recent_interactions}</strong><small>Recorded interactions</small></div>
        <div className="analytics-kpi"><span>{analytics.student_name}'s mastery</span><strong>{Math.round(analytics.overall_mastery * 100)}%</strong><small>{analytics.topics.reduce((sum, topic) => sum + topic.attempts, 0)} attempts tracked</small></div>
      </section>
      <section className="analytics-section">
        <div className="section-title"><h2>Class topic health</h2><span>Mastery and learner distribution</span></div>
        <div className="class-topic-table">
          {classAnalytics.topics.map((topic) => <div className="class-topic-row" key={topic.topic_id}>
            <div className="class-topic-name"><strong>{topic.topic_name}</strong><span>{topic.total_attempts} attempts</span></div>
            <div className="class-topic-bar"><i style={{ width: `${topic.avg_mastery * 100}%` }} /></div>
            <strong className="class-topic-percent">{Math.round(topic.avg_mastery * 100)}%</strong>
            <span className="class-topic-distribution"><b>{topic.mastered_count} mastered</b> / {topic.developing_count} developing / {topic.struggling_count} need help</span>
          </div>)}
        </div>
      </section>
      <section className="analytics-section">
        <div className="section-title"><h2>{analytics.student_name}'s trends</h2><span>Every submitted quiz answer updates this view</span></div>
        <div className="trend-grid">
          {analytics.topics.map((topic) => <article className="trend-card" key={topic.topic_id}>
            <div className="trend-card-top"><div><strong>{topic.topic_name}</strong><span>{topic.attempts} attempts / {Math.round(topic.accuracy * 100)}% accuracy</span></div><b>{Math.round(topic.current_p_know * 100)}%</b></div>
            <TrendLine points={topic.trend} />
            <span className={`status-badge status-${topic.status}`}>{topic.status}</span>
          </article>)}
        </div>
      </section>
    </main>
  );
}
