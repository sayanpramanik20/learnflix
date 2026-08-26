// Thin wrapper over the FastAPI backend. One function per endpoint, so a
// component never has to know the URL shape or repeat error handling.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const token = localStorage.getItem("ai_tutor_token");
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  register: (name, grade, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ name, grade, password }) }),
  login: (name, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ name, password }) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/students/me"),

  listTopics: () => request("/topics"),
  listTopicContents: (topicId) => request(`/topics/${topicId}/contents`),

  logInteraction: ({ studentId, contentId, correct, timeTakenSeconds = 0, rewinds = 0, quizSessionId = null }) =>
    request("/interact", {
      method: "POST",
      body: JSON.stringify({
        student_id: studentId,
        content_id: contentId,
        correct,
        time_taken_seconds: timeTakenSeconds,
        rewinds,
        quiz_session_id: quizSessionId,
      }),
    }),

  generateQuiz: (studentId, topicId) =>
    request("/quiz/generate", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, topic_id: topicId }),
    }),

  getRecommendation: (studentId) => request(`/recommend/${studentId}`),

  explain: ({ studentId, topicId, style }) =>
    request("/explain", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, topic_id: topicId, style }),
    }),

  getDashboard: (studentId) => request(`/dashboard/${studentId}`),
  getStudentAnalytics: (studentId) => request(`/analytics/student/${studentId}`),
  getClassAnalytics: () => request("/analytics/class"),
  searchTopic: (query, grade = "") =>
    request("/learn/search", {
      method: "POST",
      body: JSON.stringify({ query, grade }),
    }),
};
