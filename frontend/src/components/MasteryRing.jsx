import React from "react";

const STATUS_COLOR = {
  struggling: "var(--coral)",
  developing: "var(--amber)",
  mastered: "var(--teal)",
};

// The signature visual: a circular "mastery dial" per topic. Literally
// visualizes the knowledge-tracing probability the backend computes,
// rather than a generic progress bar — ties the UI back to what the
// system is actually doing under the hood.
export default function MasteryRing({ value, status, size = 64, strokeWidth = 6 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value);
  const color = STATUS_COLOR[status] || "var(--text-secondary)";

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mastery-ring">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--border)"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.6s ease, stroke 0.3s ease" }}
      />
      <text
        x="50%"
        y="50%"
        textAnchor="middle"
        dominantBaseline="central"
        className="mastery-ring-label"
      >
        {Math.round(value * 100)}
      </text>
    </svg>
  );
}
