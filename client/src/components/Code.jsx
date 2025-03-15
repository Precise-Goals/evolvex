import React, { useState } from "react";
import axios from "axios";

export const Code = () => {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) {
      setError("Please enter a request");
      return;
    }

    setLoading(true);
    setError("");
    setResponse("");

    try {
      const apiUrl =
        import.meta.env.VITE_API_URL || "https://evolvex.onrender.com"; // Fallback
      const res = await axios.post(`${apiUrl}/api/code`, { input });
      setResponse(res.data.response);
    } catch (err) {
      setError("Error communicating with the server: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
      <h1>Code Agent</h1>
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your coding request (e.g., 'Write a Python function to add two numbers')"
          rows="5"
          style={{ width: "100%", marginBottom: "10px" }}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Submit"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {response && (
        <div style={{ marginTop: "20px" }}>
          <h2>Response:</h2>
          <pre
            style={{
              background: "#f4f4f4",
              padding: "10px",
              borderRadius: "5px",
            }}
          >
            {response}
          </pre>
        </div>
      )}
    </div>
  );
};
