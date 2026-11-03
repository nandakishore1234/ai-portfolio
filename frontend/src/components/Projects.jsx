import { useEffect, useId, useRef, useState } from "react";
import { profile } from "../data/profile";
import "./Projects.css";

function ProjectArt({ name }) {
  if (name === "youtube") {
    return (
      <svg viewBox="0 0 640 360" aria-hidden="true">
        <rect x="78" y="58" width="360" height="230" rx="22" fill="#fff" fillOpacity="0.16" />
        <rect x="98" y="78" width="320" height="168" rx="14" fill="#0f172a" fillOpacity="0.28" />
        <circle cx="258" cy="162" r="28" fill="#fff" />
        <path d="M250 148v28l24-14z" fill="#3b82f6" />
        <rect x="118" y="258" width="90" height="10" rx="5" fill="#fff" fillOpacity="0.7" />
        <rect x="218" y="258" width="54" height="10" rx="5" fill="#fff" fillOpacity="0.4" />
        <g fill="#fff">
          <rect x="468" y="78" width="130" height="52" rx="14" fillOpacity="0.92" />
          <rect x="484" y="148" width="118" height="52" rx="14" fillOpacity="0.78" />
          <rect x="452" y="218" width="140" height="52" rx="14" fillOpacity="0.55" />
        </g>
        <circle cx="488" cy="104" r="8" fill="#3b82f6" />
        <circle cx="504" cy="174" r="8" fill="#a855f7" />
        <circle cx="472" cy="244" r="8" fill="#22c55e" />
      </svg>
    );
  }

  if (name === "resume") {
    return (
      <svg viewBox="0 0 640 360" aria-hidden="true">
        <rect x="118" y="58" width="176" height="236" rx="18" fill="#fff" fillOpacity="0.92" />
        <rect x="142" y="86" width="92" height="12" rx="6" fill="#7c3aed" fillOpacity="0.45" />
        <rect x="142" y="112" width="128" height="8" rx="4" fill="#64748b" fillOpacity="0.28" />
        <rect x="142" y="130" width="110" height="8" rx="4" fill="#64748b" fillOpacity="0.2" />
        <rect x="142" y="160" width="128" height="8" rx="4" fill="#64748b" fillOpacity="0.28" />
        <rect x="142" y="178" width="90" height="8" rx="4" fill="#64748b" fillOpacity="0.2" />
        <rect x="330" y="78" width="188" height="196" rx="18" fill="#fff" fillOpacity="0.78" />
        <rect x="354" y="106" width="110" height="12" rx="6" fill="#a855f7" fillOpacity="0.4" />
        <rect x="354" y="132" width="140" height="8" rx="4" fill="#64748b" fillOpacity="0.25" />
        <rect x="354" y="150" width="120" height="8" rx="4" fill="#64748b" fillOpacity="0.18" />
        <circle cx="424" cy="214" r="28" fill="#7c3aed" />
        <path d="M412 214l8 8 16-18" fill="none" stroke="#fff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  if (name === "local") {
    return (
      <svg viewBox="0 0 640 360" aria-hidden="true">
        <rect x="150" y="78" width="340" height="210" rx="28" fill="#fff" fillOpacity="0.14" />
        <rect x="176" y="104" width="288" height="158" rx="18" fill="#042f2e" fillOpacity="0.28" />
        <path d="M300 168v-16a20 20 0 0 1 40 0v16" fill="none" stroke="#fff" strokeWidth="8" strokeLinecap="round" />
        <rect x="286" y="164" width="68" height="48" rx="10" fill="#fff" />
        <circle cx="320" cy="186" r="6" fill="#0f766e" />
        <rect x="214" y="214" width="70" height="18" rx="9" fill="#fff" fillOpacity="0.85" />
        <rect x="294" y="214" width="92" height="18" rx="9" fill="#bbf7d0" />
        <rect x="396" y="214" width="48" height="18" rx="9" fill="#fff" fillOpacity="0.55" />
      </svg>
    );
  }

  if (name === "edge") {
    return (
      <svg viewBox="0 0 640 360" aria-hidden="true">
        <rect x="168" y="70" width="304" height="220" rx="26" fill="#fff" fillOpacity="0.16" />
        <rect x="214" y="108" width="212" height="144" rx="16" fill="#fff" fillOpacity="0.9" />
        <rect x="236" y="130" width="168" height="78" rx="10" fill="#fdba74" />
        <circle cx="268" cy="230" r="8" fill="#f97316" />
        <circle cx="298" cy="230" r="8" fill="#fb7185" />
        <circle cx="328" cy="230" r="8" fill="#22c55e" />
        <path d="M120 150h48M472 150h48M120 210h48M472 210h48M250 48v22M390 48v22M250 290v22M390 290v22" stroke="#fff" strokeWidth="8" strokeLinecap="round" />
      </svg>
    );
  }

  if (name === "kiosk") {
    return (
      <svg viewBox="0 0 640 360" aria-hidden="true">
        <rect x="86" y="48" width="468" height="248" rx="22" fill="#fff" fillOpacity="0.92" />
        <rect x="86" y="48" width="468" height="42" rx="22" fill="#dbeafe" />
        <rect x="86" y="72" width="468" height="18" fill="#dbeafe" />
        <circle cx="116" cy="69" r="6" fill="#fb7185" />
        <circle cx="138" cy="69" r="6" fill="#fbbf24" />
        <circle cx="160" cy="69" r="6" fill="#34d399" />
        <rect x="110" y="112" width="120" height="150" rx="12" fill="#eff6ff" />
        <rect x="250" y="112" width="270" height="28" rx="8" fill="#bfdbfe" />
        <rect x="250" y="154" width="210" height="16" rx="8" fill="#e2e8f0" />
        <rect x="250" y="182" width="250" height="16" rx="8" fill="#e2e8f0" />
        <rect x="250" y="222" width="110" height="36" rx="10" fill="#2563eb" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 640 360" aria-hidden="true">
      <circle cx="250" cy="180" r="92" fill="none" stroke="#fff" strokeOpacity="0.35" strokeWidth="18" />
      <circle cx="250" cy="180" r="58" fill="none" stroke="#fff" strokeOpacity="0.7" strokeWidth="14" />
      <circle cx="250" cy="180" r="22" fill="#fff" />
      <rect x="360" y="78" width="196" height="54" rx="16" fill="#fff" fillOpacity="0.92" />
      <rect x="378" y="98" width="110" height="12" rx="6" fill="#0f766e" fillOpacity="0.45" />
      <rect x="392" y="156" width="176" height="54" rx="16" fill="#fff" fillOpacity="0.75" />
      <rect x="410" y="176" width="120" height="12" rx="6" fill="#115e59" fillOpacity="0.35" />
      <rect x="348" y="232" width="160" height="54" rx="16" fill="#fff" fillOpacity="0.55" />
    </svg>
  );
}

function ProjectBody({ project, titleId }) {
  return (
    <>
      <div className={`project-media art-${project.art}`}>
        <ProjectArt name={project.art} />
      </div>
      <ul className="project-tags">
        {project.tags.map((tag) => (
          <li key={tag}>{tag}</li>
        ))}
      </ul>
      <h3 id={titleId}>{project.title}</h3>
      <p>{project.text}</p>
    </>
  );
}

export default function Projects() {
  const [active, setActive] = useState(null);
  const closeRef = useRef(null);
  const titleId = useId();

  useEffect(() => {
    if (!active) return undefined;
    const previous = document.activeElement;
    closeRef.current?.focus();
    const onKey = (event) => {
      if (event.key === "Escape") setActive(null);
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, [active]);

  return (
    <section className="projects" id="projects">
      <div className="container">
        <header className="projects-head">
          <p className="projects-kicker">Portfolio</p>
          <h2>
            Featured <span>Projects</span>
          </h2>
          <p>Recent voice agents, RAG systems, and product builds from my work.</p>
        </header>

        <div className="project-grid">
          {profile.projects.map((project) => (
            <article key={project.title} className="project-card" style={{ "--accent": project.accent }}>
              <ProjectBody project={project} />
              <div className="project-foot">
                <button type="button" className="project-link" aria-label={`View ${project.title}`} onClick={() => setActive(project)}>
                  View Project
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                    <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>

      {active && (
        <div className="project-modal" onClick={() => setActive(null)}>
          <div
            className="project-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            style={{ "--accent": active.accent }}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              ref={closeRef}
              className="project-close"
              type="button"
              aria-label="Close project details"
              onClick={() => setActive(null)}
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" strokeLinecap="round" />
              </svg>
            </button>
            <ProjectBody project={active} titleId={titleId} />
            <ul className="project-details">
              {active.details.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
