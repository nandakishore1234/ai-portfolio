import { useEffect, useState } from "react";
import "./Admin.css";

const TOKEN_KEY = "admin_jwt";

const api = (path, options = {}) => {
  const headers = { ...(options.headers || {}) };
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token && !headers.Authorization) headers.Authorization = `Bearer ${token}`;
  return fetch(path, { credentials: "include", ...options, headers });
};

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function Admin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [me, setMe] = useState("");
  const [docs, setDocs] = useState([]);
  const [assets, setAssets] = useState([]);
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  const loadDocs = async () => {
    const response = await api("/api/admin/documents");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Could not load documents.");
    setDocs(data.documents || []);
  };

  const loadAssets = async () => {
    const response = await api("/api/admin/assets");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Could not load recordings.");
    setAssets(data.assets || []);
  };

  useEffect(() => {
    (async () => {
      const response = await api("/api/admin/me");
      if (!response.ok) return;
      const data = await response.json();
      setMe(data.username || "admin");
      try {
        await loadDocs();
        await loadAssets();
      } catch (err) {
        setStatus(err instanceof Error ? err.message : "Could not load documents.");
      }
    })();
  }, []);

  const login = async (event) => {
    event.preventDefault();
    setBusy(true);
    setStatus("");
    try {
      const response = await api("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Login failed.");
      if (data.token) sessionStorage.setItem(TOKEN_KEY, data.token);
      setMe(data.username);
      setPassword("");
      await loadDocs();
      await loadAssets();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  const logout = async () => {
    await api("/api/admin/logout", { method: "POST" });
    sessionStorage.removeItem(TOKEN_KEY);
    setMe("");
    setDocs([]);
  };

  const upload = async (event) => {
    event.preventDefault();
    if (!files.length) {
      setStatus("Choose one or more .md or .txt files.");
      return;
    }
    setBusy(true);
    setStatus("");
    try {
      const body = new FormData();
      files.forEach((file) => body.append("files", file));
      const response = await api("/api/admin/documents", { method: "POST", body });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Upload failed.");
      setDocs(data.documents || []);
      setFiles([]);
      event.target.reset?.();
      setStatus(`Saved ${data.saved?.join(", ")}. Chat is reindexed. Restart the voice worker to refresh the call brain.`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (name) => {
    if (!window.confirm(`Delete ${name}?`)) return;
    setBusy(true);
    setStatus("");
    try {
      const response = await api(`/api/admin/documents/${encodeURIComponent(name)}`, { method: "DELETE" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Delete failed.");
      setDocs(data.documents || []);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="admin">
      <header className="admin-head">
        <div>
          <p className="admin-kicker">Portfolio</p>
          <h1>Knowledge admin</h1>
        </div>
        {me ? (
          <button type="button" className="admin-ghost" onClick={logout}>
            Sign out {me}
          </button>
        ) : (
          <a href="/">Back to site</a>
        )}
      </header>

      {!me ? (
        <form className="admin-card" onSubmit={login}>
          <label>
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
          {status ? <p className="admin-status">{status}</p> : null}
        </form>
      ) : (
        <>
          <form className="admin-card" onSubmit={upload}>
            <h2>Upload notes</h2>
            <p>Add one or many `.md` / `.txt` files. They join the same RAG set as `nanda.md`.</p>
            <input
              type="file"
              accept=".md,.txt,text/markdown,text/plain"
              multiple
              onChange={(event) => setFiles([...event.target.files])}
            />
            <button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Upload and reindex"}
            </button>
          </form>

          <section className="admin-card">
            <h2>Documents</h2>
            {docs.length === 0 ? <p>No files yet.</p> : null}
            <ul className="admin-list">
              {docs.map((doc) => (
                <li key={doc.name}>
                  <div>
                    <strong>{doc.name}</strong>
                    <span>{formatBytes(doc.bytes)}</span>
                  </div>
                  <button type="button" disabled={busy} onClick={() => remove(doc.name)}>
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="admin-card">
            <h2>Call recordings</h2>
            {assets.length === 0 ? <p>No recordings yet. Calls are saved to SeaweedFS when they end.</p> : null}
            <ul className="admin-list">
              {assets.map((asset) => (
                <li key={asset.id}>
                  <div>
                    <strong>{asset.kind === "call-recording" ? "Call recording" : (asset.identity || asset.kind)}</strong>
                    <span>
                      {asset.room} · {formatBytes(asset.size_bytes || 0)}
                    </span>
                  </div>
                  <audio controls preload="none" src={`/api/admin/assets/${asset.id}/audio`} />
                </li>
              ))}
            </ul>
          </section>
          {status ? <p className="admin-status">{status}</p> : null}
        </>
      )}
    </main>
  );
}
