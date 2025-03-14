import React, { useState } from "react";

export const Code = () => {
  const [input, setInput] = useState("");
  const [output, setOutput] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch("http://localhost:5000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ input }),
    });
    const data = await response.json();
    setOutput((prevOutput) => [
      ...prevOutput,
      { user: input, bot: data.response },
    ]);
    setInput("");
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message"
        />
        <button type="submit">Send</button>
      </form>
      <div>
        {output.map((item, index) => (
          <div key={index}>
            <strong>User:</strong> {item.user}
            <br />
            <strong>Bot:</strong> {item.bot}
            <hr />
          </div>
        ))}
      </div>
    </div>
  );
};
