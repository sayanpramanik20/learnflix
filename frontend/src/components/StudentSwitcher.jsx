import React from "react";

export default function StudentSwitcher({ student, onLogout }) {
  return (
    <div className="student-switcher">
      <span className="student-switcher-label">Signed in</span>
      <span className="student-identity">{student.name}{student.grade ? ` / Grade ${student.grade}` : ""}</span>
      <button className="student-logout" onClick={onLogout}>Log out</button>
    </div>
  );
}
