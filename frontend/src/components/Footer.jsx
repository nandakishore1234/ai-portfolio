import { navLinks, profile } from "../data/profile";
import "./Footer.css";

function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.28-.01-1.04-.02-2.04-3.34.72-4.04-1.61-4.04-1.61-.55-1.39-1.33-1.76-1.33-1.76-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.49 1 .11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.29-1.23 3.29-1.23.64 1.66.24 2.88.12 3.18.77.84 1.23 1.91 1.23 3.22 0 4.61-2.8 5.62-5.48 5.92.43.37.81 1.1.81 2.22 0 1.6-.01 2.9-.01 3.29 0 .32.21.69.82.57A12 12 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">
      <path d="M4.7 3.3A2.2 2.2 0 1 0 4.7 7.7 2.2 2.2 0 0 0 4.7 3.3zM3 8.7h3.4V21H3V8.7zM9.3 8.7H12.6v1.7h.1c.5-.9 1.6-1.8 3.3-1.8 3.5 0 4.2 2.3 4.2 5.3V21H16.8v-5.5c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9V21H9.3V8.7z" />
    </svg>
  );
}

const socialIcons = { GitHub: GitHubIcon, LinkedIn: LinkedInIcon };

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div className="footer-brand">
          <a className="footer-lockup" href="#home">
            <span>{profile.initials}</span>
            <strong>
              {profile.brand}
              <small>Software & AI Engineer</small>
            </strong>
          </a>
          <p>{profile.bio}</p>
          <div className="footer-social">
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

        <nav aria-label="Quick links">
          <h2>Quick Links</h2>
          <ul>
            {navLinks.map((link) => (
              <li key={link.href}>
                <a href={link.href}>{link.label}</a>
              </li>
            ))}
          </ul>
        </nav>

        <nav aria-label="Services">
          <h2>Services</h2>
          <ul>
            {profile.services.map((service) => (
              <li key={service.title}>
                <a href="#services">{service.title}</a>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      <div className="container footer-bar">
        <p>© {new Date().getFullYear()} {profile.firstName} {profile.lastName}. All rights reserved.</p>
      </div>
    </footer>
  );
}
