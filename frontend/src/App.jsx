import { useState } from "react";
import About from "./components/About";
import Admin from "./components/Admin";
import Chat from "./components/Chat";
import Contact from "./components/Contact";
import Cursor from "./components/Cursor";
import Footer from "./components/Footer";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Journey from "./components/Journey";
import Projects from "./components/Projects";
import Services from "./components/Services";
import VoiceCall from "./components/VoiceCall";
import { startCallRing } from "./lib/callRing";

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [callOpen, setCallOpen] = useState(false);
  const isAdmin = window.location.pathname.replace(/\/+$/, "") === "/admin";

  if (isAdmin) {
    return (
      <div className="page">
        <Cursor />
        <Admin />
      </div>
    );
  }

  return (
    <div className="page">
      <Cursor />
      <Header />
      <main>
        <Hero
          onChat={() => setChatOpen(true)}
          onCall={() => {
            startCallRing(5000);
            setCallOpen(true);
          }}
        />
        <About />
        <Services />
        <Projects />
        <Journey />
        <Contact />
      </main>
      <Footer />
      <Chat open={chatOpen} onClose={() => setChatOpen(false)} />
      <VoiceCall open={callOpen} onClose={() => setCallOpen(false)} />
    </div>
  );
}
