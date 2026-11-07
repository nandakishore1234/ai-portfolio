const MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID || "";

export function initAnalytics() {
  if (!MEASUREMENT_ID || window.gtag) return;
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`;
  document.head.appendChild(script);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", MEASUREMENT_ID);
}

export function track(event, params = {}) {
  if (!MEASUREMENT_ID || typeof window.gtag !== "function") return;
  window.gtag("event", event, params);
}
