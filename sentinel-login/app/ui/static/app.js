/* Vanilla UI: textContent only, theme-only localStorage, server-side i18n. */
"use strict";

const state = { locale: "es-419", strings: {} };

async function loadLocale(locale) {
  const res = await fetch(`/i18n/${locale}`);
  if (!res.ok) throw new Error("locale failed");
  state.locale = locale;
  state.strings = await res.json();
  document.documentElement.lang = locale;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPh);
  });
}

function t(key) {
  return state.strings[key] || key;
}

/* Theme: persist only the theme choice, never session data. */
function initTheme() {
  const saved = localStorage.getItem("sentinel-theme");
  if (saved) document.documentElement.dataset.theme = saved;
  document.getElementById("theme").addEventListener("click", () => {
    const next =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("sentinel-theme", next);
  });
}

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
  ["view-login", "view-chat", "view-queue", "view-admin"].forEach((v) => {
    document.getElementById(v).hidden = v !== id;
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

async function onLogin(event) {
  event.preventDefault();
  const err = document.getElementById("login-error");
  err.textContent = "";
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
  } else if (role === "advisor") {
    show("view-queue");
    loadQueue();
  } else {
    show("view-admin");
    loadAdmin();
  }
}

function addMine(text) {
  const thread = document.getElementById("thread");
  thread.append(el("div", "msg mine", text));
  thread.scrollTop = thread.scrollHeight;
}

function renderReply(body) {
  const thread = document.getElementById("thread");
  if (body.kind === "case_confirmation") {
    thread.append(receiptCard(body));
  } else if (body.kind === "handoff") {
    thread.append(handoffCard(body));
  } else if (body.kind === "clarification") {
    const box = el("div", "msg");
    box.append(el("strong", "", `${t("clarTitle")}: `));
    box.append(el("span", "", body.text));
    thread.append(box);
  } else if (body.kind === "error") {
    const box = el("div", "msg");
    box.append(el("strong", "error", `${t("errorTitle")}: `));
    box.append(el("span", "", `${body.message} (${body.trace_id})`));
    thread.append(box);
  } else {
    thread.append(el("div", "msg", body.text));
  }
  thread.scrollTop = thread.scrollHeight;
}

function receiptCard(body) {
  const card = el("div", "msg receipt");
  const head = el("h3", "", `${t("receiptTitle")} ${body.case_id} `);
  head.append(el("span", "badge-ok", t("verifiedBadge")));
  head.append(el("span", "badge-mock", t("mockBadge")));
  card.append(head);
  const tx = body.transaction;
  card.append(
    el("div", "", `${t("field_amount")}: ${tx.amount} ${tx.currency}`)
  );
  card.append(el("div", "", `${t("field_merchant")}: ${tx.merchant}`));
  card.append(el("div", "", `${t("field_date")}: ${tx.date}`));
  card.append(el("div", "", `${t("field_state")}: ${body.state}`));
  card.append(el("div", "", `${t("field_priority")}: ${body.priority}`));
  card.append(el("div", "", `${t("field_hold")}: ${body.hold}`));
  card.append(el("div", "", `${t("field_rule")}: ${body.eligibility}`));
  card.append(el("div", "", `${t("field_sla")}: ${body.sla_deadline}`));
  card.append(el("div", "", `${t("field_queue")}: ${body.queue_status}`));
  const receipt = document.createElement("a");
  receipt.href = `/api/v1/disputes/${body.case_id}/receipt`;
  receipt.download = `${body.receipt_ref}.txt`;
  receipt.textContent = `${t("downloadReceipt")} (${body.receipt_ref})`;
  card.append(receipt);
  const steps = el("ul", "timeline");
  ["step_identity", "step_found", "step_rules", "step_created", "step_confirmed"].forEach(
    (key) => steps.append(el("li", "", t(key)))
  );
  card.append(steps);
  const next = el("ul", "");
  body.next_steps.forEach((s) => next.append(el("li", "", s)));
  card.append(el("div", "", `${t("field_nextSteps")}:`));
  card.append(next);
  return card;
}

function handoffCard(body) {
  const card = el("div", "msg handoff");
  const head = el("h3", "", `${t("handoffTitle")} ${body.reference} `);
  head.append(el("span", "badge-mock", t("mockBadge")));
  card.append(head);
  card.append(el("div", "", `${t("field_reason")}: ${body.reason}`));
  card.append(el("div", "", `${t("field_received")}: ${body.advisor_received}`));
  card.append(el("div", "", `${t("field_eta")}: ${body.estimated_time}`));
  return card;
}

async function sendChat(message) {
  addMine(message);
  const res = await api("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  renderReply(await res.json());
}

async function loadQueue() {
  const res = await api("/advisor/cases");
  const { cases } = await res.json();
  const box = document.getElementById("queue");
  box.textContent = "";
  if (!cases.length) {
    box.append(el("p", "muted", t("q_empty")));
    return;
  }
  cases.forEach((c) => {
    const card = el("div", "msg handoff");
    card.append(el("h3", "", `${c.reference} (${c.case_id})`));
    card.append(el("div", "", `${t("q_customer")}: ${c.customer_id}`));
    card.append(
      el(
        "div", "",
        `${t("q_transaction")}: ${c.transaction.amount} ${c.transaction.currency} - ${c.transaction.merchant}`
      )
    );
    card.append(el("div", "", `${t("q_state")}: ${c.state}`));
    card.append(el("div", "", `${t("q_priority")}: ${c.priority}`));
    card.append(el("div", "", `${t("q_reason")}: ${c.reason}`));
    const claim = el("button", "", t("q_claim"));
    claim.addEventListener("click", async () => {
      await api(`/advisor/cases/${c.case_id}/claim`, { method: "POST" });
      loadQueue();
    });
    card.append(claim);
    box.append(card);
  });
}

async function loadAdmin() {
  const metrics = await (await api("/admin/metrics")).json();
  const box = document.getElementById("metrics");
  box.textContent = "";
  const table = el("table", "");
  Object.entries(metrics.metrics).forEach(([k, v]) => {
    const row = el("tr", "");
    row.append(el("td", "", t(`m_${k}`) === `m_${k}` ? k : t(`m_${k}`)));
    row.append(el("td", "", String(v)));
    table.append(row);
  });
  box.append(table);
  const audit = await (await api("/admin/audit")).json();
  document.getElementById("audit").textContent = JSON.stringify(audit.records, null, 2);
}

document.getElementById("login-form").addEventListener("submit", onLogin);
document.getElementById("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  if (input.value.trim()) sendChat(input.value.trim());
  input.value = "";
});
document.getElementById("agent").addEventListener("click", () => {
  sendChat("Please escalate now to an agent");
});
document.getElementById("logout").addEventListener("click", async () => {
  await fetch("/auth/logout", { method: "POST" });
  show("view-login");
});
document.getElementById("locale").addEventListener("change", (e) => {
  loadLocale(e.target.value);
});

initTheme();
loadLocale("es-419");
