/* Vanilla UI: textContent only, theme-only localStorage, server-side i18n. */
"use strict";

const THEME_KEY = "sentinel-theme";
const state = { locale: "es-419", strings: {} };

/* --- Theme: persist only the user's choice, never session data. -------- */

function systemPrefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function currentTheme() {
  return document.documentElement.dataset.theme || (systemPrefersDark() ? "dark" : "light");
}

function applyTheme(theme, persist) {
  document.documentElement.dataset.theme = theme;
  if (persist) localStorage.setItem(THEME_KEY, theme);
  const button = document.getElementById("theme");
  const dark = theme === "dark";
  button.setAttribute("aria-pressed", String(dark));
  button.textContent = "";
  const icon = el("span", "", dark ? "moon" : "sun");
  icon.id = "theme-icon";
  icon.setAttribute("aria-hidden", "true");
  button.append(icon, el("span", "sr-only", t("themeToggle")));
}

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved || (systemPrefersDark() ? "dark" : "light"), Boolean(saved));
  document.getElementById("theme").addEventListener("click", () => {
    applyTheme(currentTheme() === "dark" ? "light" : "dark", true);
  });
}

/* --- i18n: server merges the base locale with regional overrides. ------ */

async function loadLocale(locale) {
  const res = await fetch(`/i18n/${locale}`);
  if (!res.ok) throw new Error("locale failed");
  state.locale = locale;
  state.strings = await res.json();
  document.documentElement.lang = locale;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPh);
  });
}

function t(key) {
  return state.strings[key] || key;
}

/* --- DOM helpers ------------------------------------------------------- */

/* Mask digit runs of 12-16 chars, keeping the last 4 (****1234). */
function mask(value) {
  return String(value).replace(/\d{12,16}/g, (m) => `****${m.slice(-4)}`);
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = mask(text);
  return node;
}

function show(id) {
  ["view-login", "view-chat", "view-queue", "view-admin"].forEach((view) => {
    document.getElementById(view).hidden = view !== id;
  });
  document.getElementById("logout").hidden = id === "view-login";
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (res.status === 401) {
    alert(t("expiredNotice"));
    show("view-login");
    throw new Error("expired");
  }
  if (res.status === 403) {
    alert(t("deniedMessage"));
    throw new Error("denied");
  }
  return res;
}

/* --- Login ------------------------------------------------------------- */

async function onLogin(event) {
  event.preventDefault();
  const err = document.getElementById("login-error");
  err.textContent = "";
  const submit = event.target.querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: document.getElementById("login-user").value,
        password: document.getElementById("login-pass").value,
      }),
    });
    if (!res.ok) {
      err.textContent = t("deniedMessage");
      return;
    }
    const { role } = await res.json();
    if (role === "customer") {
      show("view-chat");
      await loadSessionContext();
      await loadTransactions();
    } else if (role === "advisor") {
      show("view-queue");
      loadQueue();
    } else {
      show("view-admin");
      loadAdmin();
    }
  } finally {
    submit.disabled = false;
  }
}

/* Country decides the starting language; the selector can change it after. */
async function loadSessionContext() {
  try {
    const res = await fetch("/api/v1/session/context");
    if (!res.ok) return;
    const context = await res.json();
    setReferenceDate(context.referenceDate);
    if (context.defaultLocale && context.defaultLocale !== state.locale) {
      document.getElementById("locale").value = context.defaultLocale;
      await loadLocale(context.defaultLocale);
    }
  } catch (err) {
    /* context is auxiliary: never block the chat on it */
  }
}

function setReferenceDate(iso) {
  const node = document.getElementById("reference-date");
  if (node) node.textContent = `${t("referenceDateLabel")}: ${formatDate(iso)}`;
}

/* --- Formatting: language changes presentation, never the value. -------- */

const CURRENCY_DISPLAY = "code";

function uiLocale() {
  return state.locale === "es-419" ? "es" : state.locale;
}

/* The only amount formatter in the UI: chips, panel and card all use it. */
function formatAmount(value, currency) {
  const numeric = Number(String(value).replace(/[^\d.-]/g, ""));
  if (!Number.isFinite(numeric) || !currency) return String(value);
  try {
    return new Intl.NumberFormat(uiLocale(), {
      style: "currency",
      currency,
      currencyDisplay: CURRENCY_DISPLAY,
    }).format(numeric);
  } catch (err) {
    return `${numeric} ${currency}`;
  }
}

/* The only date formatter in the UI, so no screen mixes styles. */
function formatDate(iso) {
  if (!iso) return "";
  const parsed = new Date(iso.length === 10 ? `${iso}T00:00:00Z` : iso);
  if (Number.isNaN(parsed.getTime())) return String(iso);
  return new Intl.DateTimeFormat(uiLocale(), {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(parsed);
}

/* Customer data (merchant, amounts) never passes through i18n. */
function merchantLabel(value) {
  return String(value);
}

/* --- Chat rendering ---------------------------------------------------- */

function addBubble(cls, text) {
  const thread = document.getElementById("thread");
  thread.append(el("div", `msg ${cls}`, text));
  thread.scrollTop = thread.scrollHeight;
}

function showTyping() {
  const thread = document.getElementById("thread");
  const bubble = el("div", "msg system typing");
  bubble.append(el("span", "muted", t("typingLabel")));
  thread.append(bubble);
  thread.scrollTop = thread.scrollHeight;
  return bubble;
}

function renderCandidates(box, candidates) {
  if (!candidates || !candidates.length) return;
  const chips = el("div", "chips");
  candidates.forEach((candidate) => {
    const chip = el("button", "chip");
    chip.type = "button";
    chip.textContent = `${merchantLabel(candidate.merchant)} - ${formatAmount(
      candidate.amount,
      candidate.currency
    )} (${formatDate(candidate.date)})`;
    if (!candidate.eligible) {
      chip.classList.add("chip-disabled");
      chip.disabled = true;
      chip.append(el("span", "muted", ` · ${t(candidate.ineligibleKey || "candidateOutOfWindow")}`));
    } else {
      chip.addEventListener("click", () => selectCandidate(candidate));
    }
    chips.append(chip);
  });
  box.append(chips);
}

/* The choice travels as a structured field. The transaction id never shows. */
function selectCandidate(candidate) {
  addBubble("mine", humanStatement(candidate));
  sendSelected(candidate.reference);
}

function humanStatement(candidate) {
  return `${t("referToCharge")} ${merchantLabel(candidate.merchant)} - ${formatAmount(
    candidate.amount,
    candidate.currency
  )} (${formatDate(candidate.date)})`;
}

function renderReply(body) {
  const thread = document.getElementById("thread");
  if (body.kind === "case_confirmation") {
    thread.append(receiptCard(body));
  } else if (body.kind === "handoff") {
    thread.append(handoffCard(body));
  } else if (body.kind === "clarification") {
    const box = el("div", "msg system");
    box.append(el("strong", "", `${t("clarTitle")}: `));
    box.append(el("span", "", t(body.message_key)));
    renderCandidates(box, body.candidates);
    thread.append(box);
  } else if (body.kind === "error") {
    const box = el("div", "msg system");
    box.append(el("strong", "error", `${t("errorTitle")}: `));
    box.append(el("span", "", `${t(body.message_key)} (${body.trace_id})`));
    thread.append(box);
  } else {
    thread.append(el("div", "msg", t(body.message_key)));
  }
  thread.scrollTop = thread.scrollHeight;
}

/* One proof row: icon plus label plus value. Color is never the only cue. */
function proofRow(icon, label, value) {
  const item = el("li", "");
  item.append(el("span", "proof-icon", icon));
  const body = el("div", "");
  body.append(el("span", "proof-label", label));
  body.append(el("span", "proof-value", value));
  item.append(body);
  return item;
}

function receiptCard(body) {
  const card = el("div", "msg receipt");
  const head = el("div", "receipt-head");
  head.append(
    el("h3", "", t("receiptOutcome")),
    el("span", "badge badge-success", `${t("verifiedBadge")} (OK)`),
    el("span", "badge badge-info", t("mockBadge"))
  );
  card.append(head);

  const caseLine = el("div", "case-number");
  caseLine.append(el("span", "proof-label", t("field_case")));
  caseLine.append(el("strong", "", body.case_id));
  card.append(caseLine);

  const tx = body.transaction;
  const display = body.display || {};
  const facts = el("div", "muted");
  facts.textContent = `${merchantLabel(tx.merchant)} - ${formatAmount(
    display.amount || tx.amount,
    display.currency || tx.currency
  )} (${formatDate(tx.date)})`;
  card.append(facts);

  const slaDate = formatDate(display.slaDate);
  card.append(
    el("div", "", `${t("field_next")}: ${t(body.messages.nextStep)} ${slaDate}`)
  );

  const proof = el("ul", "proof-list");
  proof.append(
    proofRow(t("proofIconRules"), t("field_rule"), t(body.messages.rule)),
    proofRow(t("proofIconQueue"), t("field_queue"), t(body.messages.queue)),
    proofRow(t("proofIconNoHold"), t("field_noFunds"), t(body.messages.noFunds))
  );
  card.append(proof);

  card.append(
    el(
      "div",
      "muted",
      `${t("field_referenceDate")}: ${formatDate(display.referenceDate)}`
    )
  );
  card.append(el("div", "muted", `${t("field_sla")}: ${slaDate}`));

  const receipt = document.createElement("a");
  receipt.className = "receipt-link";
  receipt.href = `/api/v1/disputes/${body.case_id}/receipt`;
  receipt.download = `RCPT-${body.case_id}.txt`;
  receipt.textContent = t("downloadReceipt");
  card.append(receipt);

  const steps = el("ul", "timeline");
  ["step_identity", "step_found", "step_rules", "step_created", "step_confirmed"].forEach(
    (key) => steps.append(el("li", "", t(key)))
  );
  card.append(steps);
  return card;
}

function handoffCard(body) {
  const card = el("div", "msg handoff");
  const head = el("div", "receipt-head");
  head.append(
    el("h3", "", t("handoffTitle")),
    el("span", "badge badge-warning", t("badgeEscalated"))
  );
  card.append(head);
  card.append(el("div", "", `${t("field_reason")}: ${t(body.reason_key)}`));
  if (body.reason_detail) {
    card.append(el("div", "muted", body.reason_detail));
  }
  return card;
}

async function sendChat(message) {
  addBubble("mine", message);
  await postChat({ message });
}

/* Structured selection: the reference travels in the body, validated server-side. */
async function sendSelected(reference) {
  await postChat({ selected_reference: reference });
}

async function postChat(payload) {
  const typing = showTyping();
  try {
    const res = await api("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderReply(await res.json());
  } finally {
    typing.remove();
  }
}

/* --- Transactions panel: tap a charge to dispute exactly that one. ----- */

async function loadTransactions() {
  const res = await api("/api/v1/transactions");
  const { transactions } = await res.json();
  const box = document.getElementById("transactions");
  box.textContent = "";
  if (!transactions.length) {
    box.append(el("p", "muted", t("tx_empty")));
    return;
  }
  transactions.forEach((tx) => {
    const item = el("button", "tx-item");
    item.type = "button";
    item.append(el("strong", "", formatAmount(tx.amount, tx.currency)));
    item.append(el("span", "muted", ` ${merchantLabel(tx.merchant)}`));
    item.append(el("span", "muted", ` (${formatDate(tx.date)})`));
    item.addEventListener("click", () => {
      selectCandidate(tx);
    });
    box.append(item);
  });
}

/* --- Advisor queue ----------------------------------------------------- */

async function loadQueue() {
  const res = await api("/advisor/cases");
  const { cases } = await res.json();
  const box = document.getElementById("queue");
  box.textContent = "";
  if (!cases.length) {
    box.append(el("p", "muted", t("q_empty")));
    return;
  }
  cases.forEach((item) => {
    const card = el("div", "queue-item");
    card.append(el("h3", "", `${item.reference} (${item.case_id})`));
    card.append(el("div", "muted", `${t("q_customer")}: ${item.customer_id}`));
    card.append(
      el(
        "div",
        "",
        `${t("q_transaction")}: ${merchantLabel(item.transaction.merchant)} - ${formatAmount(
          item.transaction.amount,
          item.transaction.currency
        )} (${formatDate(item.transaction.date)})`
      )
    );
    card.append(el("div", "", `${t("q_state")}: ${item.state}`));
    card.append(el("div", "", `${t("q_priority")}: ${item.priority}`));
    card.append(el("div", "muted", `${t("q_reason")}: ${item.reason}`));
    const claim = el("button", "primary-button", t("q_claim"));
    claim.addEventListener("click", async () => {
      await api(`/advisor/cases/${item.case_id}/claim`, { method: "POST" });
      loadQueue();
    });
    card.append(claim);
    box.append(card);
  });
}

/* --- Admin panel ------------------------------------------------------- */

async function loadAdmin() {
  const metrics = await (await api("/admin/metrics")).json();
  const box = document.getElementById("metrics");
  box.textContent = "";
  const table = el("table", "");
  Object.entries(metrics.metrics).forEach(([key, value]) => {
    const row = el("tr", "");
    const label = t(`m_${key}`);
    row.append(el("td", "", label === `m_${key}` ? key : label));
    row.append(el("td", "", String(value)));
    table.append(row);
  });
  box.append(table);
  const audit = await (await api("/admin/audit")).json();
  document.getElementById("audit").textContent = JSON.stringify(audit.records, null, 2);
}

/* --- Wiring ------------------------------------------------------------ */

document.getElementById("login-form").addEventListener("submit", onLogin);
document.getElementById("chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const value = input.value.trim();
  if (value) sendChat(value);
  input.value = "";
});
document.getElementById("agent").addEventListener("click", () => {
  sendChat("Please escalate now to an agent");
});
document.getElementById("logout").addEventListener("click", async () => {
  await fetch("/auth/logout", { method: "POST" });
  show("view-login");
});
document.getElementById("locale").addEventListener("change", (event) => {
  loadLocale(event.target.value);
});

initTheme();
loadLocale("es-419");
