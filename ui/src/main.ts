import "./style.css";

import { ObserverStore } from "./observer-store";

const root = document.querySelector<HTMLDivElement>("#app");
if (!root) throw new Error("Missing #app root");

root.innerHTML = `
  <main class="boot-shell">
    <p class="eyebrow">NEWLAND / OSSERVATORE LOCALE</p>
    <h1>In ascolto del territorio</h1>
    <p id="boot-status">Connessione alla memoria canonica…</p>
  </main>
`;

const apiBase = import.meta.env.VITE_OBSERVER_API ?? "http://127.0.0.1:8765";
const store = new ObserverStore(apiBase);
store.subscribe(() => {
  const status = document.querySelector<HTMLParagraphElement>("#boot-status");
  if (!status) return;
  if (store.state.error) {
    status.textContent = `Observer non raggiungibile: ${store.state.error}`;
    return;
  }
  status.textContent = `Stato: ${store.state.connection}`;
});
void store.start();
