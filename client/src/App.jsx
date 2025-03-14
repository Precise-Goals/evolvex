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
          <Route path="/evolvex-404-not-found" element={<File404 />} />
          <Route path="/evolvex-code-agentic-ai" element={<Code />} />
          <Route path="/evolvex-under-development" element={<UnderDev />} />
        </Routes>
        <Footer />
      </BrowserRouter>
    </>
  );
}

export default App;
