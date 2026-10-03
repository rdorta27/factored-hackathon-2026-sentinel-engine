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
  const value = Number(String(amount).replace(/[^\d.-]/g, ""));
  if (!Number.isFinite(value) || !currency) return `${amount} ${currency}`;
  try {
    return new Intl.NumberFormat(activeLocale(), {
      style: "currency",
      currency,
      currencyDisplay: "code",
    }).format(value);
  } catch (error) {
    return `${amount} ${currency}`;
  }
}

function formatDate(value) {
  if (!value) return "";
  const parsed = new Date(String(value).length === 10 ? `${value}T00:00:00Z` : value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat(activeLocale(), {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(parsed);
}

/* The active interface language; `es-419` maps to the plain `es` tag. */
function activeLocale() {
  const selected = document.getElementById("locale");
  const locale = selected && selected.value ? selected.value : "es-419";
  return locale === "es-419" ? "es" : locale;
}

/* The selector's own value, exactly as the API accepts it. */
function selectorLocale() {
  const selected = document.getElementById("locale");
  return selected && selected.value ? selected.value : "es-419";
}

/* Fill a template's {placeholders} without touching the rest of the text. */
function fill(template, values) {
  return Object.entries(values).reduce(
    (text, [key, value]) => text.split(`{${key}}`).join(value),
    template
  );
}

/* Explanation replies carry a key and verified values; fill placeholders here. */
function fillTemplate(template, values) {
  return String(template).replace(/\{(\w+)\}/g, (match, key) => {
    const value = values ? values[key] : undefined;
    return value === undefined || value === null ? match : String(value);
  });
}

function explanationText(body) {
  let text = fillTemplate(t(body.message_key), body.values);
  if (body.values && body.values.synthetic) {
    text = `${text} ${t("explanation.demo")}`;
  }
  return text;
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
/* Country is page-level: the chips are chosen from the listing alone, with no
   request to the chat. */
let sessionCountry = null;

async function loadContext() {
  const response = await api("/api/v1/auth/me");
  if (!response.ok) return;
  const me = await response.json();
  sessionCountry = me.country || null;
  const locale = COUNTRY_LOCALES[me.country];
  if (locale) {
    document.getElementById("locale").value = locale;
    await loadLocale(locale);
  }
}

function humanStatement(candidate) {
  return `${t("referToCharge")} ${candidate.merchant} - ${formatAmount(candidate.amount, candidate.currency)} (${formatDate(candidate.date)})`;
}

/* The receipt states the charge in the bank's voice, so the card never repeats
   what the customer typed. Same amount and date formatting as everywhere else. */
function receiptCharge(tx) {
  return fill(t("receiptCharge"), {
    merchant: tx.merchant,
    amount: formatAmount(tx.amount, tx.currency),
    date: formatDate(tx.date),
  });
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
      // The selector's language rides with every turn, so the answer comes back
      // in the language the customer chose, whatever the message looks like.
      body: JSON.stringify({ ...payload, language: selectorLocale() }),
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
    // The bank's own voice, not the customer's sentence echoed back. The
    // customer's bubble above keeps its wording; only this line changes.
    card.append(el("p", "", receiptCharge(tx)));
    card.append(el("p", "", t(body.messages.noFunds)));
    card.append(el("p", "chat-sub", `${t("field_referenceDate")}: ${formatDate(body.display.referenceDate)}`));
    thread.append(card);
  } else if (body.kind === "explanation") {
    thread.append(el("div", "msg msg-bot", explanationText(body)));
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
  renderDemoPrompts(payload.transactions);
}
/* Demo prompts: built from the customer's own charges, never hardcoded.
   Normal picks the newest charge in the account's own currency that the backend
   marks eligible, using only the listing. Eligibility already carries the
   country policy (window, status, prior dispute), so the page never re-derives
   it. If the reply on click escalates, that is a legitimate outcome and is
   shown, not hidden.
   Ambiguous picks a merchant with two or more charges, so the system asks. */
function repeatedMerchant(transactions) {
  const counts = new Map();
  transactions.forEach((tx) => counts.set(tx.merchant, (counts.get(tx.merchant) || 0) + 1));
  for (const [merchant, count] of counts) {
    if (count >= 2) return merchant;
  }
  return null;
}

/* The account's own currency, from the session country. Charges in another
   currency (the demo's USD rows) are not what the customer would dispute. */
const COUNTRY_CURRENCIES = { MX: "MXN", CO: "COP", AR: "ARS" };

function localCurrency() {
  return COUNTRY_CURRENCIES[sessionCountry] || null;
}

/* Newest eligible charge in the local currency. Eligibility is the backend's
   own country policy (window, status, prior dispute), so the page does not
   duplicate the 90-day rule. Nothing here calls the chat: the chips are chosen
   from data already on the page. */
function demoCharge(transactions) {
  const currency = localCurrency();
  if (!currency) return null;
  const candidates = (transactions || []).filter(
    (tx) => tx.eligible !== false && tx.currency === currency
  );
  return candidates.sort((a, b) => String(b.date).localeCompare(String(a.date)))[0] || null;
}

function renderDemoPrompts(transactions) {
  const box = document.getElementById("demo-prompts");
  box.textContent = "";
  const rows = transactions || [];
  const charge = demoCharge(rows);
  const merchant = repeatedMerchant(rows);
  const prompts = [];

  if (charge) {
    prompts.push(
      fill(t("demoNormal"), {
        amount: formatAmount(charge.amount, charge.currency),
        merchant: charge.merchant,
        date: formatDate(charge.date),
      })
    );
  }
  if (merchant) prompts.push(fill(t("demoAmbiguous"), { merchant }));
  prompts.push(t("demoPerson"));

  prompts.forEach((phrase) => {
    const chip = el("button", "candidate", phrase);
    chip.type = "button";
    chip.addEventListener("click", () => {
      addBubble(phrase);
      postChat({ message: phrase });
    });
    box.append(chip);
  });
  box.hidden = prompts.length === 0;
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
  await loadTransactions();
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
