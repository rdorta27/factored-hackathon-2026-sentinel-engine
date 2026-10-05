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

/* The active interface language; `es-419` maps to the plain `es` tag.
   Named buttons in #locale-group pick it; the codes never show as labels. */
let currentLocale = "es-419";

function activeLocale() {
  return currentLocale === "es-419" ? "es" : currentLocale;
}

function setLocale(locale) {
  currentLocale = locale;
  document.querySelectorAll("#locale-group [data-locale]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.getAttribute("data-locale") === locale));
  });
  const active = document.querySelector(`#locale-group [data-locale="${locale}"]`);
  const current = document.getElementById("locale-current");
  if (active && current) current.textContent = active.getAttribute("aria-label");
}

/* The selector's own value, exactly as the API accepts it. */
function selectorLocale() {
  return currentLocale;
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

/* White label: the bank name comes from the service configuration. Under
   another name the tagline says who protects the conversation. */
let brand = { name: "Sentinel", customized: false };

function applyBrand() {
  document.getElementById("brand-name").textContent = brand.name;
  document.title = brand.name;
  document.getElementById("brand-tagline").setAttribute("data-i18n", brand.customized ? "protectedBy" : "purposeLine");
  document.getElementById("brand-tagline").textContent = t(brand.customized ? "protectedBy" : "purposeLine");
}

async function loadBrand() {
  const response = await fetch("/ui/brand.json");
  if (response.ok) brand = await response.json();
  applyBrand();
}

async function loadLocale(locale) {
  const response = await fetch(`/i18n/${locale}`);
  strings = await response.json();
  setLocale(locale);
  document.documentElement.lang = locale;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.getAttribute("data-i18n"));
  });
  applyBrand();
  // A customer session repaints its header and charges in the new language.
  if (lastTransactions && !document.getElementById("view-chat").hidden) {
    renderSessionContext(lastTransactions);
    paintCharges(lastTransactions);
    renderDemoPrompts(lastTransactions.transactions);
    renderThread();
  }
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
  threadLog = [];
  document.getElementById("thread").textContent = "";
  document.getElementById("steps-side").textContent = "";
  document.getElementById("transactions").textContent = "";
  document.getElementById("cases").textContent = "";
  lastTransactions = null;
}

/* The thread is a log of what happened. Changing the language draws it again, so
   cards, steps and labels follow the new language. The customer's own words stay
   as they typed them. */
let threadLog = [];

function logEntry(entry) {
  threadLog.push(entry);
  drawEntry(entry);
  return entry;
}

function drawEntry(entry) {
  const thread = document.getElementById("thread");
  if (entry.type === "user") thread.append(el("div", "msg msg-user", entry.text));
  else if (entry.type === "charge") thread.append(el("div", "msg msg-user", humanStatement(entry.candidate)));
  else if (entry.type === "welcome") thread.append(el("div", "msg msg-bot", t("welcome")));
  else if (entry.type === "error") drawError(entry.body, entry.status);
  else if (entry.type === "reply") drawReply(entry.body, entry);
}

function renderThread() {
  document.getElementById("thread").textContent = "";
  threadLog.forEach(drawEntry);
  const last = [...threadLog].reverse().find((entry) => entry.type === "reply" && entry.body.steps);
  if (last) renderSteps(last.body, false);
}

function startThread() {
  clearThread();
  logEntry({ type: "welcome" });
}

let simulatedData = false;

function show(id) {
  ["view-login", "view-chat", "view-queue"].forEach((view) => {
    document.getElementById(view).hidden = id !== view;
  });
  document.getElementById("logout").hidden = id === "view-login";
  document.getElementById("agent").hidden = id !== "view-chat";
  // The "simulated data" banner follows Gold, not the one-click entry.
  document.getElementById("demo-banner").hidden = id !== "view-login" || !simulatedData;
  // The session line and the data date belong to a customer session only.
  if (id !== "view-chat") {
    document.getElementById("session-context").hidden = true;
    document.getElementById("reference-date").hidden = true;
    closeDrawers();
  }
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
  logEntry({ type: "user", text });
}

function renderError(body, status) {
  logEntry({ type: "error", body, status });
}

function drawError(body, status) {
  const key = status === 429 ? "tooManyRequests" : "errorGeneric";
  const trace = body && body.trace_id ? ` (${body.trace_id})` : "";
  document.getElementById("thread").append(el("div", "msg msg-audit", `${t(key)}${trace}`));
}

/* Reply kinds that write to the case store, so the charge states change. */
const CASE_CHANGING = new Set(["case_confirmation", "handoff"]);

async function postChat(payload) {
  // A new turn closes any open confirmation: an old "Confirmar" must not fire.
  document.querySelectorAll(".chat-confirm button").forEach((button) => {
    button.disabled = true;
  });
  threadLog.forEach((entry) => {
    entry.closed = true;
  });
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
    await renderReply(body);
    if (CASE_CHANGING.has(body.kind)) await refreshCharges();
  } finally {
    typing.remove();
  }
}

function selectCandidate(candidate) {
  logEntry({ type: "charge", candidate });
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

/* "Qué revisamos": the ordered steps of the last turn, in the left column.
   The keys come from the reply; the page only translates them, so no rule
   id, model or threshold ever reaches the screen. */
const HAND_STEPS = new Set(["step.handedOff", "step.refused"]);
const STEP_PAUSE_MS = 1000;
let stepTimers = [];
let stepResolve = null;

function stepItem(key, index, state) {
  const hand = HAND_STEPS.has(key) ? " step-hand" : "";
  const item = el("li", `step-item step-${state}${hand}`);
  item.append(el("span", "step-dot", state === "done" ? String(index + 1) : ""));
  const text = el("div", "step-text");
  text.append(el("span", "step-title", t(key)));
  const hint = `stepHint.${key.replace(/^step\./, "")}`;
  if (strings[hint]) text.append(el("span", "chat-sub step-hint", t(hint)));
  item.append(text);
  return item;
}

/* The reply carries the finished record of the turn. The page replays it one step
   at a time: every step starts waiting, the current one shows a spinner, and each
   turns to done after a pause. The pause is staging to follow the record, not a
   measure of the time each step took. The promise settles when the last step is done. */
function renderSteps(body, animate = true) {
  const list = document.getElementById("steps-side");
  if (!body.steps || !body.steps.length) return Promise.resolve();
  list.setAttribute("data-testid", "steps-panel");
  stepTimers.forEach(clearTimeout);
  stepTimers = [];
  // A turn that was still running gives way to this one.
  if (stepResolve) stepResolve();
  stepResolve = null;
  list.textContent = "";
  const staged = animate && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!staged) {
    body.steps.forEach((key, index) => list.append(stepItem(key, index, "done")));
    list.setAttribute("aria-busy", "false");
    return Promise.resolve();
  }
  list.setAttribute("aria-busy", "true");
  const items = body.steps.map((key, index) => {
    const item = stepItem(key, index, index === 0 ? "active" : "waiting");
    list.append(item);
    return item;
  });
  return new Promise((resolve) => {
    stepResolve = resolve;
    body.steps.forEach((key, index) => {
      stepTimers.push(
        setTimeout(() => {
          items[index].replaceWith((items[index] = stepItem(key, index, "done")));
          if (index + 1 < items.length) {
            const next = stepItem(body.steps[index + 1], index + 1, "active");
            items[index + 1].replaceWith(next);
            items[index + 1] = next;
          } else {
            list.setAttribute("aria-busy", "false");
            resolve();
          }
        }, (index + 1) * STEP_PAUSE_MS)
      );
    });
  });
}

/* Neutral transaction status: the dataset status only, never a fraud signal. */
const STATUS_KEYS = {
  Approved: "txStatusApproved",
  Pending: "txStatusPending",
  Reversed: "txStatusReversed",
  Declined: "txStatusDeclined",
};

function statusLabel(status) {
  return t(STATUS_KEYS[status] || "txStatusApproved");
}

/* A translated label for a code from the handoff package. A code the page
   does not know shows nothing, never the raw code. */
function codeLabel(prefix, code) {
  return strings[`${prefix}.${code}`] || "";
}

function cardField(labelKey, value) {
  const box = el("div", "card-field");
  box.append(el("span", "card-label", t(labelKey)), el("span", "chat-sub", value));
  return box;
}

/* The handoff card in the thread: what the advisor receives and why.
   Every value is a verified fact, a step key or a code the page translates. */
function handoffCard(body) {
  const pkg = body.package || {};
  const card = el("div", "msg msg-audit handoff-card");
  card.setAttribute("data-testid", "handoff-card");
  const head = el("div", "handoff-head");
  head.append(el("span", "pill pill-warn", t("handoffCardTitle")));
  head.append(el("span", "handoff-ref", `${t("field_reference")}: ${body.reference}`));
  card.append(head);
  const grid = el("div", "card-grid");
  const request = codeLabel("handoffRequest", pkg.request);
  if (request) grid.append(cardField("handoffRequest", request));
  const facts = pkg.verified_facts;
  if (facts) {
    const parts = [facts.merchant, formatAmount(Number(facts.amount).toFixed(2), facts.currency), formatDate(facts.transaction_date)];
    grid.append(cardField("handoffFacts", parts.filter(Boolean).join(" · ")));
  }
  const actions = (body.steps || []).filter((key) => key !== "step.understood").map((key) => t(key));
  if (actions.length) grid.append(cardField("handoffActions", actions.join(" · ")));
  grid.append(cardField("handoffReason", t(body.reason_key)));
  const said = [...new Set((pkg.conversation || []).map((turn) => codeLabel("handoffSaid", turn.customer)))].filter(Boolean);
  if (said.length) grid.append(cardField("handoffSaid", said.join(" · ")));
  const pending = (pkg.open_questions || []).map((code) => codeLabel("handoffOpen", code)).filter(Boolean);
  if (pending.length) grid.append(cardField("handoffPending", pending.join(" · ")));
  card.append(grid);
  if (body.estimated_date) {
    card.append(el("p", "chat-sub", `${t("field_eta")}: ${formatDate(body.estimated_date)}`));
  }
  return card;
}

/* "Por qué decidí esto": the rule behind a refusal, with the verified dates. */
function whyCard(body) {
  const values = body.values;
  if (!values || !values.window_days) return null;
  const card = el("div", "msg msg-audit why-card");
  card.setAttribute("data-testid", "why-card");
  card.append(el("strong", "", t("whyCardTitle")));
  card.append(el("p", "", fillTemplate(t("whyWindow"), values)));
  const grid = el("div", "card-grid");
  if (values.charge_date) grid.append(cardField("whyChargeDate", formatDate(values.charge_date)));
  if (values.last_eligible_date) grid.append(cardField("whyLastDay", formatDate(values.last_eligible_date)));
  card.append(grid);
  return card;
}

/* The steps run first and the answer follows, so the customer sees the work
   before the result. */
async function renderReply(body) {
  await renderSteps(body, true);
  logEntry({ type: "reply", body, closed: false });
}

function drawReply(body, entry) {
  const thread = document.getElementById("thread");
  if (body.kind === "confirm_box") {
    const box = el("div", "chat-confirm");
    const item = body.candidate;
    box.append(el("p", "", t(body.message_key)));
    box.append(el("p", "", humanStatement(item)));
    const button = el("button", "", t("confirmButton"));
    button.type = "button";
    button.disabled = Boolean(entry && entry.closed);
    button.addEventListener("click", () => {
      // One confirmation per box: the button turns off as soon as it is used.
      button.disabled = true;
      if (entry) entry.closed = true;
      postChat({ selected_reference: item.reference });
    });
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
    thread.append(el("div", "msg msg-bot", body.text ? body.text : explanationText(body)));
    const why = whyCard(body);
    if (why) thread.append(why);
  } else if (body.kind === "clarification") {
    const box = el("div", "msg msg-audit");
    box.append(el("strong", "", body.text ? body.text : fillTemplate(t(body.message_key), body.values)));
    renderCandidates(box, body.candidates);
    thread.append(box);
  } else if (body.kind === "handoff") {
    thread.append(handoffCard(body));
  } else if (body.kind === "error") {
    thread.append(el("div", "msg msg-audit", `${t(body.message_key)} (${body.trace_id})`));
  } else {
    thread.append(el("div", "msg msg-bot", body.text ? body.text : t(body.message_key)));
  }
}

/* The pill of a charge. The state comes from the server; the page only
   chooses a word and a tone. A charge the policy rejects by status shows
   the dataset status, as before. */
const STATE_TONES = {
  eligible: "info",
  in_review: "info",
  with_advisor: "warn",
  already_disputed: "neutral",
  outside_window: "neutral",
  not_disputable: "neutral",
};

function stateLabel(tx) {
  if (tx.case_state && tx.case_state !== "not_disputable") return t(`state.${tx.case_state}`);
  return statusLabel(tx.status);
}

function renderCharge(tx) {
  const item = el("button", `candidate tx-card${tx.case_state === "in_review" ? " tx-active" : ""}`);
  item.type = "button";
  item.setAttribute("data-testid", "tx-card");
  item.setAttribute("data-case-state", tx.case_state || "");
  const top = el("span", "tx-line");
  top.append(el("strong", "", tx.merchant));
  top.append(el("strong", "", formatAmount(maskValue(tx.amount), tx.currency)));
  const bottom = el("span", "tx-line");
  bottom.append(el("span", "chat-sub", formatDate(tx.date)));
  bottom.append(el("span", `pill pill-${STATE_TONES[tx.case_state] || "neutral"} tx-status`, stateLabel(tx)));
  item.append(top, bottom);
  if (!tx.eligible) {
    item.disabled = true;
    item.setAttribute("aria-disabled", "true");
    item.title = t(tx.ineligibleKey || "candidateOutOfWindow");
  } else {
    item.addEventListener("click", () => {
      closeDrawers();
      selectCandidate(tx);
    });
  }
  return item;
}

/* The header line of a session: the masked product when the data has one,
   then country and language. Without a product the line has no type and no digits. */
function renderSessionContext(payload) {
  const parts = [];
  if (payload.product) parts.push(`${t(`product.${payload.product.kind}`)} •••• ${payload.product.last4}`);
  if (sessionCountry) parts.push(t(`country.${sessionCountry}`));
  parts.push(t(`lang.${currentLocale}`));
  const line = document.getElementById("session-context");
  line.textContent = parts.join(" · ");
  line.hidden = false;
  const chip = document.getElementById("reference-date");
  chip.textContent = fill(t("dataAsOf"), { date: formatDate(payload.as_of) });
  chip.hidden = false;
}

let lastTransactions = null;

/* "Mis reclamos": the cases of this customer, from the case store. */
function renderCases(cases) {
  const box = document.getElementById("cases");
  box.textContent = "";
  if (!cases.length) {
    box.append(el("p", "chat-sub", t("casesEmpty")));
    return;
  }
  cases.forEach((item) => {
    const card = el("div", "case-card");
    card.setAttribute("data-testid", "case-card");
    const top = el("span", "tx-line");
    top.append(el("strong", "case-id", item.case_id));
    top.append(el("span", `pill pill-${STATE_TONES[item.case_state] || "neutral"}`, t(`state.${item.case_state}`)));
    card.append(top);
    const what = [item.merchant, item.amount ? formatAmount(item.amount, item.currency) : "", item.date ? formatDate(item.date) : ""];
    card.append(el("span", "chat-sub", what.filter(Boolean).join(" · ")));
    box.append(card);
  });
}

function paintCharges(payload) {
  lastTransactions = payload;
  renderCases(payload.cases || []);
  const box = document.getElementById("transactions");
  box.textContent = "";
  payload.transactions.forEach((tx) => box.append(renderCharge(tx)));
}

async function loadTransactions() {
  const response = await api("/api/v1/transactions");
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    renderError(payload, response.status);
    return;
  }
  renderSessionContext(payload);
  paintCharges(payload);
  renderDemoPrompts(payload.transactions);
}

/* Charges change when a reply opens a case or a handoff ticket. */
async function refreshCharges() {
  const response = await api("/api/v1/transactions");
  if (!response.ok) return;
  const payload = await response.json().catch(() => null);
  if (!payload) return;
  paintCharges(payload);
}

/* Side panels: columns on a wide screen, a drawer behind a button on a phone. */
function closeDrawers() {
  document.querySelectorAll(".side-panel.drawer-open").forEach((panel) => panel.classList.remove("drawer-open"));
  document.querySelectorAll("[data-drawer]").forEach((button) => button.setAttribute("aria-expanded", "false"));
}

function toggleDrawer(button) {
  const panel = document.getElementById(button.getAttribute("data-drawer"));
  const open = !panel.classList.contains("drawer-open");
  closeDrawers();
  panel.classList.toggle("drawer-open", open);
  button.setAttribute("aria-expanded", String(open));
}

document.querySelectorAll("[data-drawer]").forEach((button) => {
  button.addEventListener("click", () => toggleDrawer(button));
});
document.querySelectorAll("[data-close-drawer]").forEach((button) => {
  button.addEventListener("click", closeDrawers);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeDrawers();
});

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
  const blocked = rows.find((tx) => tx.case_state === "outside_window" && tx.currency === localCurrency());
  if (blocked) prompts.push(fill(t("demoWhy"), { merchant: blocked.merchant }));
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
  document.getElementById("demo-hint").hidden = prompts.length === 0;
}

/* Advisor view: escalated tickets, newest first. The list shows why each case
   came (reason, country, language, age); the detail is read-only and adds the
   handoff package and the trace of the turn that filed it. */
function ticketRow(ticket) {
  const row = el("button", "candidate queue-row");
  row.type = "button";
  row.setAttribute("data-testid", "queue-row");
  row.setAttribute("data-case-id", ticket.case_id);
  row.append(el("strong", "", ticket.case_id));
  row.append(el("span", "chat-sub", ` · ${t("q_reason")}: ${t(ticket.reason_key)}`));
  row.append(el("span", "chat-sub", ` · ${t("q_country")}: ${ticket.country}`));
  row.append(el("span", "chat-sub", ` · ${t("q_language")}: ${ticket.package.language}`));
  row.append(el("span", "chat-sub", ` · ${t("q_created")}: ${formatDate(ticket.created_at)}`));
  row.addEventListener("click", () => openTicket(ticket.case_id));
  return row;
}

async function loadQueue() {
  const response = await api("/api/v1/handoffs");
  if (!response.ok) return;
  const tickets = await response.json();
  document.getElementById("queue-detail").hidden = true;
  document.getElementById("queue-list").hidden = false;
  const box = document.getElementById("queue");
  box.textContent = "";
  if (!tickets.length) box.append(el("p", "chat-sub", t("q_empty")));
  tickets.forEach((ticket) => box.append(ticketRow(ticket)));
}

function field(labelKey, value) {
  return el("p", "", `${t(labelKey)}: ${value}`);
}

function traceBlock(trace) {
  const card = el("div", "msg msg-audit");
  card.append(el("h4", "chat-title", t("q_trace")));
  if (!trace.available) {
    card.append(el("p", "chat-sub", t("q_traceUnavailable")));
    return card;
  }
  const list = el("ul", "chat-sub");
  trace.steps.forEach((step) => {
    const parts = [
      step.step,
      step.tool,
      step.outcome,
      `${t("q_latency")}: ${Number(step.latency_ms).toFixed(1)}`,
      `${t("q_model")}: ${step.model}`,
      `${t("q_prompt")}: ${step.prompt_version}`,
      `${t("q_cost")}: ${Number(step.cost_usd).toFixed(4)}`,
    ];
    if (step.policy_version) parts.push(`${t("q_policyVersion")}: ${step.policy_version}`);
    list.append(el("li", "", parts.filter(Boolean).join(" · ")));
  });
  card.append(list);
  return card;
}

/* The conversation of the ticket as translated lines: what the customer did and
   what the system answered. The server sends codes, never the customer's words. */
function turnsBlock(turns) {
  const box = el("div", "");
  box.append(el("p", "", t("q_summary")));
  const list = el("ol", "chat-sub");
  turns.forEach((turn) => {
    const said = codeLabel("handoffSaid", turn.customer);
    const answered = codeLabel("turnSystem", turn.system);
    list.append(el("li", "", [said, answered].filter(Boolean).join(" → ")));
  });
  box.append(list);
  return box;
}

function packageBlock(pkg) {
  const card = el("div", "msg msg-audit");
  card.append(el("h4", "chat-title", t("q_package")));
  card.append(turnsBlock(pkg.conversation || []));
  const facts = pkg.verified_facts;
  if (facts) {
    card.append(
      field(
        "q_transaction",
        `${facts.merchant} - ${formatAmount(Number(facts.amount).toFixed(2), facts.currency)} (${formatDate(facts.transaction_date)})`
      )
    );
  }
  const actions = el("ul", "chat-sub");
  pkg.actions_taken.forEach((action) => {
    const parts = [`#${action.turn}`, action.step, action.tool, action.outcome, action.policy_rule].filter(Boolean);
    actions.append(el("li", "", `${parts.join(" · ")} (${action.attempt})`));
  });
  card.append(el("p", "", t("q_actions")));
  card.append(actions);
  const pending = pkg.open_questions.map((code) => codeLabel("handoffOpen", code)).filter(Boolean);
  card.append(field("q_openQuestions", pending.join(", ")));
  return card;
}

async function openTicket(caseId) {
  const detail = document.getElementById("queue-detail");
  const response = await api(`/api/v1/handoffs/${caseId}`);
  if (!response.ok) return;
  const ticket = await response.json();
  const traceResponse = await api(`/api/v1/handoffs/${caseId}/trace`);
  const trace = traceResponse.ok ? await traceResponse.json() : { available: false, steps: [] };
  detail.textContent = "";
  const back = el("button", "theme-toggle", t("q_back"));
  back.type = "button";
  back.setAttribute("data-testid", "queue-back");
  back.addEventListener("click", loadQueue);
  detail.append(back);
  detail.append(el("h3", "chat-title", `${ticket.case_id} · ${codeLabel("ticketStatus", ticket.status) || ticket.status}`));
  // No customer identifier on the screen: the advisor gets facts, not an id.
  detail.append(field("q_country", `${ticket.country} · ${t("q_language")}: ${ticket.package.language}`));
  detail.append(field("q_reason", t(ticket.reason_key)));
  detail.append(packageBlock(ticket.package));
  detail.append(traceBlock(trace));
  document.getElementById("queue-list").hidden = true;
  detail.hidden = false;
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
  startThread();
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

document.getElementById("locale-group").addEventListener("click", (event) => {
  const button = event.target.closest("[data-locale]");
  if (button) loadLocale(button.getAttribute("data-locale"));
});

/* Demo entry: one-click personas behind SENTINEL_DEMO_AUTH. The page asks
   GET /api/v1/auth/demo: 200 lists the personas (banner + buttons shown,
   password form left as a secondary link), 404 hides them and opens the
   password form. The persona id is the only thing sent; no identifier. */
async function loadDemoEntry() {
  const response = await fetch("/api/v1/auth/demo");
  const available = response.ok;
  document.getElementById("demo-personas").hidden = !available;
  document.getElementById("password-login").open = !available;
}

/* The "simulated data" notice follows Gold, not the one-click entry. It shows
   on the entry page whenever Gold is a mock, with or without the personas. */
async function loadDataNotice() {
  const response = await fetch("/api/v1/health");
  if (!response.ok) return;
  const body = await response.json().catch(() => ({}));
  simulatedData = body.gold_source === "mock";
  document.getElementById("demo-banner").hidden = !simulatedData || document.getElementById("view-login").hidden;
}

async function demoLogin(persona) {
  const response = await fetch(`/api/v1/auth/demo/${persona}`, { method: "POST" });
  if (!response.ok) {
    document.getElementById("login-error").textContent = t("loginFailed");
    return;
  }
  const { locale } = await response.json();
  startThread();
  show("view-chat");
  await loadContext();
  if (locale) await loadLocale(locale);
  await loadTransactions();
}

document.getElementById("demo-personas").addEventListener("click", (event) => {
  const button = event.target.closest("[data-persona]");
  if (button) demoLogin(button.getAttribute("data-persona"));
});

loadLocale("es-419");
loadBrand();
loadDemoEntry();
loadDataNotice();
