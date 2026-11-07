const RING_MS = 5000;

let audio;
let stopTimer;

export function startCallRing(ms = RING_MS) {
  stopCallRing();
  audio = new Audio("/ring.mp3");
  audio.loop = true;
  audio.volume = 1;
  void audio.play().catch(() => {});
  stopTimer = window.setTimeout(stopCallRing, ms);
}

export function stopCallRing() {
  if (stopTimer) {
    window.clearTimeout(stopTimer);
    stopTimer = undefined;
  }
  if (!audio) return;
  audio.pause();
  audio.currentTime = 0;
  audio = null;
}
