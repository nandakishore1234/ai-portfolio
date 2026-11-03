import { hireHref, profile } from "../data/profile";
import "./About.css";

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M12 4v10m0 0 4-4m-4 4-4-4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 18h14" strokeLinecap="round" />
    </svg>
  );
}

export default function About() {
  const { about } = profile;

  return (
    <section className="about" id="about">
      <div className="container">
        <header className="about-head">
          <p className="about-kicker">{about.eyebrow}</p>
          <h2>
            {about.titleLead} <span>{about.titleAccent}</span>
          </h2>
          <p>{about.intro}</p>
        </header>

        <div className="about-grid">
          <div className="about-visual">
            <img src="/nanda.jpg" alt="Portrait of Nanda Kishore" />
            <article className="about-float about-years">
              <span className="about-ring">
                <span className="about-ring-stroke" aria-hidden="true" />
                <strong>{about.highlights[0].value}</strong>
              </span>
              <span>
                <small>{about.highlights[0].label}</small>
              </span>
            </article>
          </div>

          <div className="about-copy">
            <h3>
              {about.headlineLead} <span>{about.headlineAccent}</span>
            </h3>
            {about.paragraphs.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}

            <div className="about-actions">
              <a className="about-btn about-btn-primary" href={hireHref}>
                Hire Me
                <ArrowIcon />
              </a>
              <a className="about-btn about-btn-ghost" href={about.cv} download>
                <DownloadIcon />
                Download CV
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
