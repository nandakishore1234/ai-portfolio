import { useEffect, useState } from "react";
import { profile } from "../data/profile";
import "./Contact.css";

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M8 3h3l1.5 4-2 1.5a12 12 0 0 0 5 5L17 12l4 1.5V17a2 2 0 0 1-2 2A15 15 0 0 1 5 5a2 2 0 0 1 2-2z" strokeLinejoin="round" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" strokeLinecap="round" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.28-.01-1.04-.02-2.04-3.34.72-4.04-1.61-4.04-1.61-.55-1.39-1.33-1.76-1.33-1.76-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.49 1 .11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.29-1.23 3.29-1.23.64 1.66.24 2.88.12 3.18.77.84 1.23 1.91 1.23 3.22 0 4.61-2.8 5.62-5.48 5.92.43.37.81 1.1.81 2.22 0 1.6-.01 2.9-.01 3.29 0 .32.21.69.82.57A12 12 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
      <path d="M4.7 3.3A2.2 2.2 0 1 0 4.7 7.7 2.2 2.2 0 0 0 4.7 3.3zM3 8.7h3.4V21H3V8.7zM9.3 8.7H12.6v1.7h.1c.5-.9 1.6-1.8 3.3-1.8 3.5 0 4.2 2.3 4.2 5.3V21H16.8v-5.5c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9V21H9.3V8.7z" />
    </svg>
  );
}

const icons = { mail: MailIcon, phone: PhoneIcon, spark: SparkIcon };

const channels = [
  { key: "mail", label: "Email", value: profile.email, href: `mailto:${profile.email}`, color: "#3b82f6" },
  { key: "phone", label: "Phone", value: profile.phone, href: "tel:+918281588640", color: "#a855f7" },
  { key: "spark", label: "Availability", value: profile.availability, color: "#14b8a6" },
];

const socialIcons = { GitHub: GitHubIcon, LinkedIn: LinkedInIcon };

const emptyForm = {
  name: "",
  email: "",
  subject: "",
  message: "",
};

const hireForm = {
  name: "",
  email: "",
  subject: "Hiring inquiry",
  message: "Hi Nanda,\n\nI'd like to discuss a role / freelance opportunity with you.\n\n",
};

function readIntent() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("intent") === "hire") return "hire";
  if (window.location.hash.includes("intent=hire")) return "hire";
  return "";
}

export default function Contact() {
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const applyIntent = () => {
      if (readIntent() === "hire") {
        setForm((current) => ({
          ...hireForm,
          name: current.name,
          email: current.email,
        }));
        window.setTimeout(() => {
          const send = document.getElementById("contact-send");
          send?.scrollIntoView({ behavior: "smooth", block: "center" });
          send?.focus();
        }, 350);
      }
    };

    applyIntent();
    window.addEventListener("hashchange", applyIntent);
    window.addEventListener("popstate", applyIntent);
    return () => {
      window.removeEventListener("hashchange", applyIntent);
      window.removeEventListener("popstate", applyIntent);
    };
  }, []);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setStatus("");
    setError("");
    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim(),
          subject: form.subject.trim(),
          message: form.message.trim(),
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : "Could not send the message.";
        throw new Error(detail);
      }
      setStatus(data.detail || "Message sent. I'll get back to you soon.");
      setForm((current) => ({
        ...emptyForm,
        subject: readIntent() === "hire" ? hireForm.subject : "",
        message: readIntent() === "hire" ? hireForm.message : "",
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the message.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="contact" id="contact">
      <div className="container">
        <header className="contact-head">
          <p>Get In Touch</p>
          <h2>
            Let's Work <span>Together</span>
          </h2>
          <p>Have a project in mind? Let's discuss how I can help bring your ideas to life.</p>
        </header>

        <div className="contact-grid">
          <div className="contact-copy">
            <h3>Let's talk about your project</h3>
            <p>
              I'm always interested in hearing about new projects and opportunities. Whether you have a
              question or just want to say hi, feel free to reach out.
            </p>
            <ul>
              {channels.map((channel) => {
                const Icon = icons[channel.key];
                const inner = (
                  <>
                    <span className="channel-icon" style={{ background: channel.color }}>
                      <Icon />
                    </span>
                    <span>
                      <small>{channel.label}</small>
                      <strong>{channel.value}</strong>
                    </span>
                  </>
                );
                return (
                  <li key={channel.label}>
                    {channel.href ? (
                      <a href={channel.href}>{inner}</a>
                    ) : (
                      <div className="channel-static">{inner}</div>
                    )}
                  </li>
                );
              })}
            </ul>
            <div className="contact-social">
              <span>Follow me on social media</span>
              <div>
                {profile.socials.map((item) => {
                  const Icon = socialIcons[item.label];
                  return (
                    <a key={item.label} href={item.href} target="_blank" rel="noreferrer" aria-label={item.label}>
                      <Icon />
                    </a>
                  );
                })}
              </div>
            </div>
          </div>

          <form className="contact-form" onSubmit={onSubmit}>
            <div className="field-row">
              <label htmlFor="contact-name">
                Your Name
                <input
                  id="contact-name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  placeholder="Your name"
                  value={form.name}
                  onChange={onChange}
                  required
                />
              </label>
              <label htmlFor="contact-email">
                Your Email
                <input
                  id="contact-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@email.com"
                  value={form.email}
                  onChange={onChange}
                  required
                />
              </label>
            </div>
            <label htmlFor="contact-subject">
              Subject
              <input
                id="contact-subject"
                name="subject"
                type="text"
                placeholder="Project inquiry"
                value={form.subject}
                onChange={onChange}
                required
              />
            </label>
            <label htmlFor="contact-message">
              Message
              <textarea
                id="contact-message"
                name="message"
                rows="5"
                placeholder="Tell me about your project."
                value={form.message}
                onChange={onChange}
                required
              />
            </label>
            <button id="contact-send" type="submit" disabled={busy}>
              {busy ? "Sending…" : "Send Message"}
              <span aria-hidden="true">→</span>
            </button>
            {status ? <p className="contact-status">{status}</p> : null}
            {error ? <p className="contact-status contact-status-error">{error}</p> : null}
          </form>
        </div>
      </div>
    </section>
  );
}
