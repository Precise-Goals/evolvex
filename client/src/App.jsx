import React, { useEffect, useRef, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./App.css";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { File404 } from "./components/File404";
import { Code } from "./components/Code";
import { UnderDev } from "./components/UnderDev";
import { Hero } from "./components/Hero";
import { CiVolumeHigh, CiVolumeMute } from "react-icons/ci";

import mp3 from "./assets/bg.mp3";
import { Documentation } from "./components/Documentation";
function App() {
  const [isMuted, setIsMuted] = useState(true);

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const BackgroundSound = () => {
    const audioRef = React.useRef(null);

    useEffect(() => {
      if (audioRef.current) {
        audioRef.current.muted = isMuted;
        if (!isMuted) {
          audioRef.current
            .play()
            .catch((e) => console.log("Autoplay prevented:", e));
        }
      }
    }, [isMuted]);
    return (
      <>
        <audio ref={audioRef} src={mp3} loop autoPlay muted={isMuted}>
          Your browser does not support the audio element.
        </audio>

        <button onClick={toggleMute} className="sound-toggle">
          {isMuted ? <CiVolumeMute /> : <CiVolumeHigh />}
        </button>
      </>
    );
  };

  return (
    <>
      <BackgroundSound />
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Hero />} />
          <Route path="*" element={<File404 />} />
          <Route path="/evolvex-code-agentic-ai" element={<Code />} />
          <Route path="/evolvex-creative-agentic-ai" element={<UnderDev />} />
          <Route path="/evolvex-student-agentic-ai" element={<UnderDev />} />
          <Route path="/evolvex-business-agentic-ai" element={<UnderDev />} />
          <Route path="/evolvex-documentation" element={<Documentation />} />
        </Routes>
        <Footer />
      </BrowserRouter>
    </>
  );
}

export default App;
