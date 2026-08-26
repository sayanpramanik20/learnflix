import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function MicroQuiz({ open, studentId, topicId, topicName, onClose, onComplete }) {
  const [question, setQuestion] = useState(null);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [startedAt, setStartedAt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function loadQuestion() {
    setLoading(true);
    setError(null);
    setSelected(null);
    setResult(null);
    try {
      const next = await api.generateQuiz(studentId, topicId);
      setQuestion(next);
      setStartedAt(Date.now());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open && studentId && topicId) loadQuestion();
  }, [open, studentId, topicId]);

  if (!open) return null;

  async function submitAnswer() {
    if (selected === null || !question || result) return;
    const correct = selected === question.answer_index;
    try {
      setLoading(true);
      await api.logInteraction({
        studentId,
        contentId: question.content_id,
        correct,
        timeTakenSeconds: Math.round((Date.now() - startedAt) / 1000),
        quizSessionId: `micro-${Date.now()}`,
      });
      setResult({ correct });
      onComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="quiz-backdrop" role="presentation" onClick={onClose}>
      <section className="quiz-modal" role="dialog" aria-modal="true" aria-labelledby="quiz-title" onClick={(event) => event.stopPropagation()}>
        <div className="quiz-header">
          <div>
            <span className="eyebrow">Micro-quiz / {topicName}</span>
            <h2 id="quiz-title">Check your thinking</h2>
          </div>
          <button className="tutor-panel-close" onClick={onClose} aria-label="Close quiz">×</button>
        </div>
        {error && <div className="banner banner-error">{error}</div>}
        {loading && !question ? <p className="quiz-muted">Building a question...</p> : question && (
          <>
            <p className="quiz-question">{question.question}</p>
            <div className="quiz-options">
              {question.options.map((option, index) => (
                <button
                  key={option}
                  className={`quiz-option ${selected === index ? "quiz-option-selected" : ""} ${result && index === question.answer_index ? "quiz-option-correct" : ""} ${result && selected === index && !result.correct ? "quiz-option-wrong" : ""}`}
                  onClick={() => setSelected(index)}
                  disabled={Boolean(result) || loading}
                >
                  <span className="quiz-option-letter">{String.fromCharCode(65 + index)}</span>
                  <span>{option}</span>
                </button>
              ))}
            </div>
            {result ? (
              <div className={`quiz-feedback ${result.correct ? "quiz-feedback-good" : "quiz-feedback-bad"}`}>
                <strong>{result.correct ? "Correct." : "Not quite."}</strong>
                <span>{question.explanation}</span>
              </div>
            ) : (
              <button className="btn btn-primary quiz-submit" disabled={selected === null || loading} onClick={submitAnswer}>
                Submit answer
              </button>
            )}
            {result && <button className="btn btn-ghost quiz-next" onClick={loadQuestion}>Try another question</button>}
          </>
        )}
      </section>
    </div>
  );
}
