import { useEffect, useId, useRef, useState } from "react";
import { profile } from "../data/profile";
import "./Chat.css";

const starters = [
  {
    text: "What kind of work do you do?",
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <rect x="9" y="3" width="6" height="11" rx="3" />
        <path d="M6 11a6 6 0 0 0 12 0M12 17v3" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    text: "Tell me about your voice AI experience",
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <rect x="7" y="7" width="10" height="10" rx="2" />
        <path d="M9 3v4M12 3v4M15 3v4M9 17v4M12 17v4M15 17v4M3 9h4M3 12h4M3 15h4M17 9h4M17 12h4M17 15h4" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    text: "Which projects should I look at?",
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path d="M12 3 3 8l9 5 9-5-9-5Z" strokeLinejoin="round" />
        <path d="m3 12 9 5 9-5M3 16l9 5 9-5" strokeLinejoin="round" />
      </svg>
    ),
  },
];

function Mark() {
  return <span className="chat-mark">{profile.initials}</span>;
}

function Arrow() {
  return (
    <svg className="chat-starter-arrow" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M5 12h12M13 7l5 5-5 5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Chat({ open, onClose }) {
  const titleId = useId();
  const inputRef = useRef(null);
  const threadRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const started = messages.length > 0;

  useEffect(() => {
    if (!open) return undefined;
    const previous = document.activeElement;
    inputRef.current?.focus();
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, [open, onClose]);

  useEffect(() => {
    const thread = threadRef.current;
    if (thread) thread.scrollTop = thread.scrollHeight;
  }, [messages, busy, open]);

  if (!open) return null;

  const send = async (text) => {
    const content = text.trim();
    if (!content || busy) return;
    const next = [...messages, { role: "user", content }];
    setMessages(next);
    setDraft("");
    setBusy(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : "I couldn't reach the assistant.";
        throw new Error(detail);
      }
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.reply, sources: data.sources || [] },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "Something went wrong. Please try again.",
          sources: [],
        },
      ]);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  const onSubmit = (event) => {
    event.preventDefault();
    send(draft);
  };

  return (
    <div className="chat-modal" onClick={onClose}>
      <section
        className={`chat-dialog${started ? " chat-dialog-started" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <button className="chat-close" type="button" aria-label="Close chat" onClick={onClose}>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
            <path d="M6 6l12 12M18 6 6 18" strokeLinecap="round" />
          </svg>
        </button>

        <div className="chat-thread" ref={threadRef}>
          <div className="chat-intro">
            <Mark />
            <h2 id={titleId}>
              Hi, I'm {profile.firstName} <span aria-hidden="true">👋</span>
            </h2>
            <p>Ask me about voice AI, RAG, or the systems I've built.</p>
            <div className="chat-starters">
              {starters.map((item) => (
                <button key={item.text} type="button" disabled={busy} onClick={() => send(item.text)}>
                  <span className="chat-starter-icon">{item.icon}</span>
                  <span>{item.text}</span>
                  <Arrow />
                </button>
              ))}
            </div>
          </div>

          {started && (
            <div className="chat-messages">
              {messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={`chat-bubble chat-bubble-${message.role}`}>
                  {message.role === "assistant" && <Mark />}
                  <div>
                    <p>{message.content}</p>
                  </div>
                </article>
              ))}
              {busy && (
                <article className="chat-bubble chat-bubble-assistant chat-bubble-status" aria-live="polite">
                  <Mark />
                  <div>
                    <p className="chat-status">
                      <span className="chat-status-dots" aria-hidden="true">
                        <span />
                        <span />
                        <span />
                      </span>
                      <span className="chat-status-label">Thinking</span>
                    </p>
                  </div>
                </article>
              )}
            </div>
          )}
        </div>

        <form className="chat-form" onSubmit={onSubmit}>
          <span className="chat-spark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M12 2.5 13.4 8 19 9.4 13.4 10.8 12 16.4 10.6 10.8 5 9.4 10.6 8 12 2.5Z" />
              <path d="M18 14.2 18.7 16.5 21 17.2 18.7 17.9 18 20.2 17.3 17.9 15 17.2 17.3 16.5 18 14.2Z" />
            </svg>
          </span>
          <label className="sr-only" htmlFor="chat-input">
            Message
          </label>
          <input
            id="chat-input"
            ref={inputRef}
            value={draft}
            placeholder="Ask me something..."
            onChange={(event) => setDraft(event.target.value)}
            disabled={busy}
          />
          <span className="chat-clip" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M8 12.5 14.2 6.3a3 3 0 0 1 4.2 4.2l-7.8 7.8a4.2 4.2 0 0 1-6-6L12 4.9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <button className="chat-send" type="submit" disabled={busy || !draft.trim()} aria-label="Send message">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
              <path d="M3.2 11.3 19.6 3.6c.8-.4 1.6.5 1.2 1.3L14.6 20c-.4.8-1.5.8-1.9 0l-2.6-5.2-5.2-2.6c-.8-.4-.8-1.5 0-1.9Z" />
            </svg>
          </button>
        </form>
      </section>
    </div>
  );
}
