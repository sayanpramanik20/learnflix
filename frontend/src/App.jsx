import React, { useEffect, useState, useCallback } from "react";
import { api } from "./api.js";
import StudentSwitcher from "./components/StudentSwitcher.jsx";
import RecommendedHero from "./components/RecommendedHero.jsx";
import TopicList from "./components/TopicList.jsx";
import TutorPanel from "./components/TutorPanel.jsx";
import MicroQuiz from "./components/MicroQuiz.jsx";
import AnalyticsDashboard from "./components/AnalyticsDashboard.jsx";
import TopicSearch from "./components/TopicSearch.jsx";
import AuthScreen from "./components/AuthScreen.jsx";

export default function App() {
  const [student, setStudent] = useState(null);
  const studentId = student?.id;
  const [dashboard, setDashboard] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [recMessage, setRecMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelTopicId, setPanelTopicId] = useState(null);
  const [panelTopicName, setPanelTopicName] = useState("");
  const [panelLoading, setPanelLoading] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [styleUsed, setStyleUsed] = useState(null);
  const [view, setView] = useState("learner");
  const [quizOpen, setQuizOpen] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [classAnalytics, setClassAnalytics] = useState(null);

  // ---- data loading ----

  const refreshForStudent = useCallback(async (id) => {
    if (!id) return;
    setError(null);
    try {
      const [dash, rec] = await Promise.all([
        api.getDashboard(id),
        api.getRecommendation(id).catch((err) => ({ __message: err.message })),
      ]);
      setDashboard(dash);
      if (rec.__message) {
        setRecommendation(null);
        setRecMessage(rec.__message);
      } else {
        setRecommendation(rec);
        setRecMessage(null);
      }
      const [studentAnalytics, classroomAnalytics] = await Promise.all([
        api.getStudentAnalytics(id),
        api.getClassAnalytics(),
      ]);
      setAnalytics(studentAnalytics);
      setClassAnalytics(classroomAnalytics);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        if (localStorage.getItem("ai_tutor_token")) {
          setStudent(await api.me());
        }
      } catch (err) {
        setError(
          `Couldn't reach the backend at the configured API URL. Is uvicorn running? (${err.message})`
        );
      }
    })();
  }, []);

  useEffect(() => {
    if (studentId) refreshForStudent(studentId);
  }, [studentId, refreshForStudent]);

  // ---- actions ----

  async function handleLogout() {
    await api.logout().catch(() => {});
    localStorage.removeItem("ai_tutor_token");
    setStudent(null);
    setDashboard(null);
  }

  async function openExplain(topicId, preferredStyle) {
    const topic = dashboard?.topics.find((t) => t.topic_id === topicId);
    setPanelTopicId(topicId);
    setPanelTopicName(topic ? topic.topic_name : "");
    setPanelOpen(true);
    await fetchExplanation(topicId, preferredStyle);
  }

  async function fetchExplanation(topicId, style) {
    setPanelLoading(true);
    setError(null);
    try {
      const res = await api.explain({ studentId, topicId, style });
      setExplanation(res.explanation);
      setStyleUsed(res.style_used);
    } catch (err) {
      setError(err.message);
    } finally {
      setPanelLoading(false);
    }
  }

  function handlePickStyle(style) {
    if (!panelTopicId) return;
    fetchExplanation(panelTopicId, style);
  }

  // ---- render ----

  if (!student) return <AuthScreen onAuthenticated={setStudent} />;

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">∞</span>
          <span className="brand-name">Learnflix</span>
        </div>
        <StudentSwitcher
          student={student}
          onLogout={handleLogout}
        />
        <nav className="view-switcher" aria-label="App view">
          <button className={view === "learner" ? "view-active" : ""} onClick={() => setView("learner")}>Learner</button>
          <button className={view === "analytics" ? "view-active" : ""} onClick={() => setView("analytics")}>Teacher analytics</button>
        </nav>
      </header>

      {error && <div className="banner banner-error">{error}</div>}

      {!studentId ? (
        <div className="empty-state">
          <p>Add a student above to get started.</p>
        </div>
      ) : (
        view === "analytics" ? (
          <AnalyticsDashboard
            analytics={analytics}
            classAnalytics={classAnalytics}
            students={[student]}
            selectedStudentId={studentId}
            onStudentChange={() => {}}
          />
        ) : <main className="app-main">
          <TopicSearch grade={student.grade} />
          <RecommendedHero
            recommendation={recommendation}
            message={recMessage}
            busy={busy}
            onStartQuiz={() => setQuizOpen(true)}
            onExplain={openExplain}
          />

          {dashboard && (
            <>
              <div className="overall-mastery">
                Overall mastery <span className="mono">{Math.round(dashboard.overall_mastery * 100)}%</span>
              </div>
              <TopicList topics={dashboard.topics} onExplain={(id) => openExplain(id)} />
            </>
          )}
        </main>
      )}

      <TutorPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
        topicName={panelTopicName}
        loading={panelLoading}
        explanation={explanation}
        styleUsed={styleUsed}
        onPickStyle={handlePickStyle}
      />
      <MicroQuiz
        open={quizOpen}
        studentId={studentId}
        topicId={recommendation?.topic_id}
        topicName={recommendation?.topic_name}
        onClose={() => setQuizOpen(false)}
        onComplete={() => refreshForStudent(studentId)}
      />
    </div>
  );
}
