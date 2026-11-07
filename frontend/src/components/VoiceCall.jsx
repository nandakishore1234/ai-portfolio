import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Room, RoomEvent, Track } from "livekit-client";
import { profile } from "../data/profile";
import { track } from "../lib/analytics";
import { stopCallRing } from "../lib/callRing";
import "./VoiceCall.css";

function formatTime(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function Wave({ side, active }) {
  const bars = useMemo(() => [10, 18, 26, 14, 22, 30, 16, 24, 12, 20, 28, 15], []);
  return (
    <div className={`voice-wave voice-wave-${side}${active ? " is-active" : ""}`} aria-hidden="true">
      {bars.map((height, index) => (
        <span key={`${side}-${index}`} style={{ "--h": `${height}px`, "--d": `${index * 0.08}s` }} />
      ))}
    </div>
  );
}

export default function VoiceCall({ open, onClose }) {
  const titleId = useId();
  const roomRef = useRef(null);
  const readyRef = useRef(false);
  const [seconds, setSeconds] = useState(0);
  const [muted, setMuted] = useState(false);
  const [status, setStatus] = useState("Connecting…");
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [remoteSpeaking, setRemoteSpeaking] = useState(false);
  const [needsSoundTap, setNeedsSoundTap] = useState(false);

  useEffect(() => {
    if (!open) return undefined;
    setSeconds(0);
    setMuted(false);
    setStatus("Ringing…");
    setReady(false);
    readyRef.current = false;
    setError("");
    setRemoteSpeaking(false);
    setNeedsSoundTap(false);

    let cancelled = false;
    const room = new Room({ adaptiveStream: true, dynacast: true });
    roomRef.current = room;

    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);

    const markReady = () => {
      if (cancelled || readyRef.current) return;
      readyRef.current = true;
      stopCallRing();
      setReady(true);
      setSeconds(0);
      setStatus("Talking with Nanda");
      track("voice_call_start");
    };

    const attachRemoteAudio = (track) => {
      const el = track.attach();
      el.dataset.livekitAudio = "1";
      el.autoplay = true;
      el.playsInline = true;
      el.muted = false;
      el.volume = 1;
      document.body.appendChild(el);
      const play = el.play();
      if (play && typeof play.catch === "function") {
        play.catch(() => {
          if (!cancelled) setNeedsSoundTap(true);
        });
      }
    };

    room.on(RoomEvent.TrackSubscribed, (track, _publication, participant) => {
      if (track.kind !== Track.Kind.Audio) return;
      attachRemoteAudio(track);
      if (!participant.isLocal) markReady();
    });
    room.on(RoomEvent.TrackUnsubscribed, (track) => {
      track.detach().forEach((el) => el.remove());
    });
    room.on(RoomEvent.ParticipantConnected, (participant) => {
      if (!cancelled && !participant.isLocal && !readyRef.current) {
        setStatus("Ringing…");
      }
    });
    room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      const local = room.localParticipant?.identity;
      setRemoteSpeaking(speakers.some((speaker) => speaker.identity !== local));
    });
    room.on(RoomEvent.Disconnected, () => {
      if (cancelled) return;
      stopCallRing();
      setStatus("Disconnected");
      track("voice_call_end");
      window.setTimeout(() => {
        if (!cancelled) onClose();
      }, 1200);
    });

    const setupTimeout = window.setTimeout(() => {
      if (!cancelled && !readyRef.current) {
        setError("The assistant took too long to join. Please try again.");
        setStatus("Call failed");
      }
    }, 60000);

    (async () => {
      try {
        const response = await fetch("/api/livekit/token", { method: "POST" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(typeof data.detail === "string" ? data.detail : "Could not get a call token.");
        }
        if (cancelled) return;
        await room.connect(data.url, data.token);
        if (cancelled) {
          await room.disconnect();
          return;
        }
        try {
          await room.startAudio();
        } catch {
          if (!cancelled) setNeedsSoundTap(true);
        }
        // Stay on Connecting until agent audio arrives; enable mic in the background.
        try {
          await Promise.race([
            room.localParticipant.setMicrophoneEnabled(true),
            new Promise((_, reject) => {
              window.setTimeout(() => reject(new Error("Microphone permission timed out")), 8000);
            }),
          ]);
        } catch {
          if (!cancelled) setMuted(true);
        }
        // If the agent was already in the room with audio, catch up.
        room.remoteParticipants.forEach((participant) => {
          participant.audioTrackPublications.forEach((publication) => {
            if (publication.track) {
              attachRemoteAudio(publication.track);
              markReady();
            }
          });
        });
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not start the call.");
        setStatus("Call failed");
      }
    })();

    return () => {
      cancelled = true;
      stopCallRing();
      window.clearTimeout(setupTimeout);
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
      document.querySelectorAll("[data-livekit-audio]").forEach((el) => el.remove());
      room.disconnect();
      roomRef.current = null;
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open || error || !ready) return undefined;
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [open, error, ready]);

  useEffect(() => {
    const room = roomRef.current;
    if (!room || !ready) return;
    room.localParticipant.setMicrophoneEnabled(!muted).catch(() => {});
  }, [muted, ready]);

  if (!open) return null;

  const talking = ready && !muted && !error && (remoteSpeaking || status.startsWith("Talking"));
  const connecting = !error && !ready;

  const enableSound = async () => {
    try {
      await roomRef.current?.startAudio();
      document.querySelectorAll("[data-livekit-audio]").forEach((el) => {
        el.muted = false;
        void el.play?.();
      });
      setNeedsSoundTap(false);
    } catch {
      setNeedsSoundTap(true);
    }
  };

  const endCall = () => {
    stopCallRing();
    roomRef.current?.disconnect();
    onClose();
  };

  return (
    <div className="voice-modal" onClick={endCall}>
      <section
        className="voice-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="voice-header">
          <div className="voice-agent">
            <span className="voice-mark">{profile.initials}</span>
            <div>
              <strong id={titleId}>Nanda AI Agent</strong>
              <p>
                <span className="voice-live" aria-hidden="true" />
                Voice Assistant
              </p>
            </div>
          </div>
          <button className="voice-close" type="button" aria-label="Close call" onClick={endCall}>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
              <path d="M6 6l12 12M18 6 6 18" strokeLinecap="round" />
            </svg>
          </button>
        </header>

        <div className="voice-stage">
          <Wave side="left" active={talking} />
          <div className={`voice-avatar-ring${talking ? " is-talking" : ""}`}>
            <img src="/nanda.jpg" alt={profile.firstName} />
          </div>
          <Wave side="right" active={talking} />
        </div>

        <div className="voice-status">
          <h3>
            {error ? "Call unavailable" : muted && ready ? "You're muted" : status}{" "}
            {!error && !muted && status.startsWith("Talking") ? <span aria-hidden="true">✨</span> : null}
          </h3>
          <p>{error || (connecting ? "Ringing…" : formatTime(seconds))}</p>
          {needsSoundTap && !error ? (
            <button className="voice-sound-tap" type="button" onClick={enableSound}>
              Tap to hear audio
            </button>
          ) : null}
        </div>

        <div className="voice-controls" role="group" aria-label="Call controls">
          <button
            type="button"
            className={`voice-control${muted ? " is-on" : ""}`}
            aria-pressed={muted}
            disabled={Boolean(error) || connecting}
            onClick={() => setMuted((value) => !value)}
          >
            <span className="voice-control-btn" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8">
                <rect x="9" y="3" width="6" height="11" rx="3" />
                <path d="M6 11a6 6 0 0 0 12 0M12 17v3" strokeLinecap="round" />
                {muted ? <path d="M5 5l14 14" strokeLinecap="round" /> : null}
              </svg>
            </span>
            Mute
          </button>

          <button type="button" className="voice-control voice-control-end" onClick={endCall}>
            <span className="voice-control-btn" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                <path d="M6.6 16.8c1.8 1.8 4.4 2.9 7.2 2.9h1.4a1.4 1.4 0 0 0 1.4-1.3l.2-2.1a1.2 1.2 0 0 0-.8-1.2l-2.2-.8a1.2 1.2 0 0 0-1.3.4l-.7.8a10.2 10.2 0 0 1-3.8-3.8l.8-.7a1.2 1.2 0 0 0 .4-1.3l-.8-2.2a1.2 1.2 0 0 0-1.2-.8l-2.1.2A1.4 1.4 0 0 0 3.7 8.2V9.6c0 2.8 1.1 5.4 2.9 7.2Z" transform="rotate(135 12 12)" />
              </svg>
            </span>
            End Call
          </button>
        </div>
      </section>
    </div>
  );
}
