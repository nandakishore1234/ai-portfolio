import { profile } from "../data/profile";
import "./Journey.css";

export default function Journey() {
  return (
    <section className="journey" id="experience">
      <div className="container journey-layout">
        <header>
          <p>My Experience</p>
          <h2>
            My Professional
            <span>Journey</span>
          </h2>
        </header>

        <ol className="timeline">
          {profile.journey.map((job) => (
            <li key={job.org} className="job">
              <span className="job-mark" style={{ background: job.color }} aria-hidden="true">
                {job.mark}
              </span>
              <div>
                <h3>
                  {job.role}
                  <span> — {job.org}</span>
                </h3>
                <p>{job.text}</p>
              </div>
              <time dateTime={job.start}>{job.date}</time>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
