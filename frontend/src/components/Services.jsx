import { profile } from "../data/profile";
import "./Services.css";

function ServiceIcon({ name }) {
  const common = {
    viewBox: "0 0 24 24",
    width: "22",
    height: "22",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    "aria-hidden": "true",
  };

  if (name === "voice") {
    return (
      <svg {...common}>
        <path d="M12 4v16M8 8v8M16 8v8M4 10v4M20 10v4" strokeLinecap="round" />
      </svg>
    );
  }

  if (name === "rag") {
    return (
      <svg {...common}>
        <path d="M8 7h11M8 12h11M8 17h7" strokeLinecap="round" />
        <circle cx="5" cy="7" r="1" fill="currentColor" stroke="none" />
        <circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" />
        <circle cx="5" cy="17" r="1" fill="currentColor" stroke="none" />
      </svg>
    );
  }

  if (name === "api") {
    return (
      <svg {...common}>
        <ellipse cx="12" cy="7" rx="7" ry="3" />
        <path d="M5 7v10c0 1.7 3.1 3 7 3s7-1.3 7-3V7" />
        <path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3" />
      </svg>
    );
  }

  if (name === "agent") {
    return (
      <svg {...common}>
        <rect x="7" y="8" width="10" height="9" rx="2" />
        <path d="M12 8V5M9 13h.01M15 13h.01M9 19l-1 2M15 19l1 2" strokeLinecap="round" />
      </svg>
    );
  }

  if (name === "edge") {
    return (
      <svg {...common}>
        <rect x="8" y="8" width="8" height="8" rx="1.5" />
        <path d="M10 4.5v3.5M14 4.5v3.5M10 16v3.5M14 16v3.5M4.5 10H8M4.5 14H8M16 10h3.5M16 14h3.5" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg {...common}>
      <path d="M13 3 5 13h6l-1 8 8-11h-6l1-7z" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export default function Services() {
  return (
    <section className="services" id="services">
      <div className="container">
        <header className="services-head">
          <p>Services</p>
          <h2>
            What I <span>Offer</span>
          </h2>
          <p>AI systems, voice agents, and backend services built for production.</p>
        </header>

        <div className="service-grid">
          {profile.services.map((service) => (
            <article key={service.title} className="service-card" style={{ "--wash": service.tint }}>
              <span className="service-icon" style={{ background: service.color }}>
                <ServiceIcon name={service.icon} />
              </span>
              <h3>{service.title}</h3>
              <p>{service.text}</p>
              <ul>
                {service.points.map((point) => (
                  <li key={point}>
                    <span aria-hidden="true" style={{ color: service.color }}>✓</span>
                    {point}
                  </li>
                ))}
              </ul>
              <a href="#contact" style={{ color: service.color }}>
                Learn More
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
