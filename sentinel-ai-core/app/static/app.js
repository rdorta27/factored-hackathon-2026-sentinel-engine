let strings = {};

function t(key) {
  return strings[key] || key;
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function maskValue(value) {
  const text = String(value);
  const digits = text.replace(/\D/g, "");
  if (digits.length >= 12) return `****${digits.slice(-4)}`;
  return text;
}

function formatAmount(amount, currency) {
  return `${amount} ${currency}`;
}

function formatDate(value) {
  return String(value);
}

async function loadLocale(locale) {
  const response = await fetch(`/i18n/${locale}`);
  strings = await response.json();
  document.documentElement.lang = locale;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.getAttribute("data-i18n"));
  });
}

async function api(path, options) {
  const response = await fetch(path, options);
  if (response.status === 401) {
    clearThread();
    show("view-login");
    document.getElementById("login-error").textContent = t("sessionExpired");
  }
  return response;
}

function clearThread() {
  document.getElementById("thread").textContent = "";
}

function show(id) {
  ["view-login", "view-chat", "view-queue"].forEach((view) => {
    document.getElementById(view).hidden = id !== view;
  });
  document.getElementById("logout").hidden = id === "view-login";
}

/* The session country picks the starting language; the selector can change it. */
const COUNTRY_LOCALES = { MX: "es-MX", CO: "es-CO", AR: "es-AR" };

async function loadContext() {
  const response = await api("/api/v1/auth/me");
  if (!response.ok) return;
  const me = await response.json();
  const locale = COUNTRY_LOCALES[me.country];
  if (locale) {
    document.getElementById("locale").value = locale;
    await loadLocale(locale);
  }
}

function humanStatement(candidate) {
  return `${t("referToCharge")} ${candidate.merchant} - ${formatAmount(candidate.amount, candidate.currency)} (${formatDate(candidate.date)})`;
}

function addBubble(text) {
  document.getElementById("thread").append(el("div", "msg msg-user", text));
}

function renderError(body, status) {
  const key = status === 429 ? "tooManyRequests" : "errorGeneric";
  const trace = body && body.trace_id ? ` (${body.trace_id})` : "";
  document.getElementById("thread").append(el("div", "msg msg-audit", `${t(key)}${trace}`));
}

async function postChat(payload) {
  const typing = el("div", "msg msg-audit", t("typingLabel"));
  document.getElementById("thread").append(typing);
  try {
    const response = await api("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      renderError(body, response.status);
      return;
    }
    renderReply(body);
  } finally {
    typing.remove();
  }
}

function selectCandidate(candidate) {
  addBubble(humanStatement(candidate));
  postChat({ selected_reference: candidate.reference });
}

function renderCandidates(box, candidates) {
  const chips = el("div", "chat-candidates");
  (candidates || []).forEach((candidate) => {
    const chip = el("button", "candidate", humanStatement(candidate));
    chip.type = "button";
    if (!candidate.eligible) {
      chip.disabled = true;
      chip.append(el("span", "chat-sub", ` ${t(candidate.ineligibleKey || "candidateOutOfWindow")}`));
    } else {
      chip.addEventListener("click", () => selectCandidate(candidate));
    }
    chips.append(chip);
  });
  box.append(chips);
}

function renderReply(body) {
  const thread = document.getElementById("thread");
  if (body.kind === "confirm_box") {
    const box = el("div", "chat-confirm");
    const item = body.candidate;
    box.append(el("p", "", t(body.message_key)));
    box.append(el("p", "", humanStatement(item)));
    const button = el("button", "", t("confirmButton"));
    button.type = "button";
    button.addEventListener("click", () => postChat({ selected_reference: item.reference }));
    box.append(button);
    thread.append(box);
  } else if (body.kind === "case_confirmation") {
    const card = el("div", "msg msg-audit");
    card.append(el("h3", "chat-title", t("receiptOutcome")));
    card.append(el("strong", "", body.case_id));
    const tx = body.transaction;
    card.append(el("p", "", humanStatement(tx)));
    card.append(el("p", "", t(body.messages.noFunds)));
    card.append(el("p", "chat-sub", `${t("field_referenceDate")}: ${formatDate(body.display.referenceDate)}`));
    thread.append(card);
  } else if (body.kind === "clarification") {
    const box = el("div", "msg msg-audit");
    box.append(el("strong", "", t(body.message_key)));
    renderCandidates(box, body.candidates);
    thread.append(box);
  } else if (body.kind === "handoff") {
    const card = el("div", "msg msg-audit");
    card.append(el("h3", "chat-title", t("handoffTitle")));
    card.append(el("p", "", `${t("field_reference")}: ${body.reference}`));
    card.append(el("p", "", `${t("field_reason")}: ${t(body.reason_key)}`));
    if (body.estimated_date) {
      card.append(el("p", "chat-sub", `${t("field_eta")}: ${formatDate(body.estimated_date)}`));
    }
    thread.append(card);
  } else if (body.kind === "error") {
    thread.append(el("div", "msg msg-audit", `${t(body.message_key)} (${body.trace_id})`));
  } else {
    thread.append(el("div", "msg msg-bot", t(body.message_key)));
  }
}

async function loadTransactions() {
  const response = await api("/api/v1/transactions");
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    renderError(payload, response.status);
    return;
  }
  document.getElementById("reference-date").textContent = `${t("field_referenceDate")}: ${formatDate(payload.as_of)}`;
  const box = document.getElementById("transactions");
  box.textContent = "";
  payload.transactions.forEach((tx) => {
    const item = el("button", "candidate");
    item.type = "button";
    item.append(el("strong", "", formatAmount(maskValue(tx.amount), tx.currency)));
    item.append(el("span", "chat-sub", ` ${tx.merchant}`));
    item.append(el("span", "chat-sub", ` (${formatDate(tx.date)})`));
    if (!tx.eligible) {
      item.disabled = true;
      item.append(el("span", "chat-sub", ` ${t(tx.ineligibleKey || "candidateOutOfWindow")}`));
    } else {
      item.addEventListener("click", () => selectCandidate(tx));
    }
    box.append(item);
  });
}

/* Advisor view: the escalated tickets with why they came and what was tried. */
function ticketCard(ticket) {
  const pkg = ticket.package;
  const card = el("div", "msg msg-audit");
  card.append(el("h3", "chat-title", `${ticket.case_id} · ${ticket.status}`));
  card.append(el("p", "chat-sub", `${t("q_customer")}: ${ticket.customer_id} · ${t("q_country")}: ${ticket.country}`));
  const rule = pkg.evidence && pkg.evidence.policy_rule ? ` (${pkg.evidence.policy_rule})` : "";
  card.append(el("p", "", `${t("q_reason")}: ${t(ticket.reason_key)}${rule}`));
  card.append(el("p", "", `${t("q_summary")}: ${pkg.summary}`));
  const facts = pkg.verified_facts;
  if (facts) {
    card.append(
      el("p", "", `${t("q_transaction")}: ${facts.merchant} - ${formatAmount(Number(facts.amount).toFixed(2), facts.currency)} (${formatDate(facts.transaction_date)}) · ${facts.transaction_id}`)
    );
  }
  const actions = el("ul", "chat-sub");
  pkg.actions_taken.forEach((action) => {
    const parts = [`#${action.turn}`, action.step, action.tool, action.outcome, action.policy_rule].filter(Boolean);
    actions.append(el("li", "", `${parts.join(" · ")} (${action.attempt})`));
  });
  card.append(el("p", "", t("q_actions")));
  card.append(actions);
  card.append(el("p", "", `${t("q_openQuestions")}: ${pkg.open_questions.join(", ")}`));
  return card;
}

async function loadQueue() {
  const response = await api("/api/v1/handoffs");
  if (!response.ok) return;
  const tickets = await response.json();
  const box = document.getElementById("queue");
  box.textContent = "";
  if (!tickets.length) box.append(el("p", "chat-sub", t("q_empty")));
  tickets.forEach((ticket) => box.append(ticketCard(ticket)));
}

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      login: document.getElementById("login-user").value,
      password: document.getElementById("login-pass").value,
    }),
  });
  if (!response.ok) {
    document.getElementById("login-error").textContent = t("loginFailed");
    return;
  }
  const { role } = await response.json();
  if (role === "advisor") {
    show("view-queue");
    loadQueue();
    return;
  }
  clearThread();
  show("view-chat");
  await loadContext();
  loadTransactions();
});

document.getElementById("chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const value = input.value.trim();
  if (!value) return;
  addBubble(value);
  postChat({ message: value });
  input.value = "";
});

document.getElementById("agent").addEventListener("click", () => {
  const message = t("agentMessage");
  addBubble(t("agentButton"));
  postChat({ message });
});

document.getElementById("logout").addEventListener("click", async () => {
  await fetch("/api/v1/auth/logout", { method: "POST" });
  clearThread();
  show("view-login");
});

document.getElementById("locale").addEventListener("change", (event) => {
  loadLocale(event.target.value);
});

loadLocale("es-419");
