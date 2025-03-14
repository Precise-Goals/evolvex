import React from "react";
import { Link } from "react-router-dom";

export const Navbar = () => {
  return (
    <div className="navb">
      <nav className="nav">
        <div className="rg">
          <Link to="/">Home</Link>
          <Link to="/evolvex-documentation">Docs</Link>
          <Link to="/evolvex-code-agentic-ai">Developer</Link>
        </div>
        <Link to="/">
          <h1 className="logo">Evolvex</h1>
        </Link>
        <div className="lg">
          <Link to="/evolvex-business-agentic-ai">Business</Link>
          <Link to="/evolvex-student-agentic-ai">Student</Link>
          <Link to="/evolvex-creative-agentic-ai">Creative</Link>
        </div>
      </nav>
    </div>
  );
};
