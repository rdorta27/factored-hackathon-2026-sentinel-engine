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

/* The build line links the page to the measured build: the model, the prompt
   version, the first 8 characters of the bundle hash and the Gold source. It
   reads the public health endpoint once, needs no session and writes no state.
   The line stays hidden when the request fails; the chat does not depend on it. */
let buildInfo = null;

function renderBuildInfo() {
  if (!buildInfo) return;
  const line = document.getElementById("build-info");
  line.textContent = [
    `${t("buildInfoModel")}: ${buildInfo.model}`,
    `${t("buildInfoPrompt")}: ${buildInfo.prompt_version}`,
    `${t("buildInfoBuild")}: ${String(buildInfo.bundle_hash || "").slice(0, 8)}`,
    `${t("buildInfoGold")}: ${buildInfo.gold_source}`,
  ].join(" · ");
  line.hidden = false;
}

async function loadBuildInfo() {
  try {
    const response = await fetch("/api/v1/health");
    if (!response.ok) return;
    buildInfo = await response.json();
    renderBuildInfo();
  } catch (error) {
    // The line stays hidden; the chat does not depend on the build line.
  }
}

/* Two quick clicks on the selector: only the last request may paint. */
let localeRequest = 0;

async function loadLocale(locale) {
  const request = ++localeRequest;
  const response = await fetch(`/i18n/${locale}`);
  if (!response.ok) return;
  const loaded = await response.json();
  if (request !== localeRequest) return;
  strings = loaded;
  document.body.removeAttribute("data-loading");
  setLocale(locale);
  document.documentElement.lang = locale;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.getAttribute("data-i18n"));
  });
  document.getElementById("chat-input").placeholder = t("chatPlaceholder");
  document.getElementById("chat-input").setAttribute("aria-label", t("chatPlaceholder"));
  applyBrand();
  renderBuildInfo();
  // A customer session repaints its header and charges in the new language.
  if (lastTransactions && !document.getElementById("view-chat").hidden) {
    renderSessionContext(lastTransactions);
    paintCharges(lastTransactions);
    renderDemoPrompts(lastTransactions.transactions);
  }
  // The advisor list and the open case follow the language too.
  if (!document.getElementById("view-queue").hidden) {
    loadQueue();
    if (openCaseId) openTicket(openCaseId);
    else showQueueList();
  }
  // The thread follows the language too, even before the charges arrive
  // (the welcome of a demo persona is drawn before its locale loads).
  if (!document.getElementById("view-chat").hidden) renderThread();
}

async function api(path, options) {
  const response = await fetch(path, options);
  if (response.status === 401) {
    sessionRole = null;
    sessionLabel = null;
    replaceRoute("/");
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
  casesShowAll = false;
}

/* The thread is a log of what happened. Changing the language draws it again, so
   cards, steps and labels follow the new language. The customer's own words stay
   as they typed them. */
let threadLog = [];

function logEntry(entry) {
  threadLog.push(entry);
  drawEntry(entry);
  scrollToEnd();
  return entry;
}

function drawEntry(entry) {
  const thread = document.getElementById("thread");
  if (entry.type === "user") thread.append(el("div", "msg msg-user", entry.text));
  else if (entry.type === "charge") thread.append(el("div", "msg msg-user", humanStatement(entry.candidate)));
  else if (entry.type === "welcome") thread.append(el("div", "msg msg-bot", t("welcome")));
  else if (entry.type === "error") drawError(entry.body, entry.status);
  else if (entry.type === "reply") drawReply(entry.body, entry);
  else if (entry.type === "info") document.getElementById("thread").append(chargeInfoCard(entry.tx));
}

function renderThread() {
  document.getElementById("thread").textContent = "";
  threadLog.forEach(drawEntry);
  // A turn in flight keeps its typing line and its running steps.
  if (typingNode) {
    typingNode.textContent = t("typingLabel");
    document.getElementById("thread").append(typingNode);
    return;
  }
  const last = [...threadLog].reverse().find((entry) => entry.type === "reply" && entry.body.steps);
  if (last) renderSteps(last.body, false);
}

/* Keep the newest message in view. */
function scrollToEnd() {
  const thread = document.getElementById("thread");
  const last = thread.lastElementChild;
  if (last) last.scrollIntoView({ block: "end", behavior: "smooth" });
}

function startThread() {
  clearThread();
  logEntry({ type: "welcome" });
}

let simulatedData = false;
/* The one-click personas are on: the chat then offers example prompts. */
let demoAvailable = false;

function show(id) {
  // An old login error must not wait on screen for the next visit.
  if (id !== "view-login") document.getElementById("login-error").textContent = "";
  ["view-login", "view-chat", "view-queue"].forEach((view) => {
    document.getElementById(view).hidden = id !== view;
  });
  if (id !== "view-queue") stopQueueRefresh();
  document.getElementById("logout").hidden = id === "view-login";
  // The agent button lives in the chat column, away from the header flags.
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

/* One turn at a time: while a turn runs, every control that sends a turn is
   off, so a double click or an impatient tap cannot send it twice. */
let typingNode = null;

function isBusy() {
  return typingNode !== null;
}

function setBusy(busy) {
  document.getElementById("view-chat").setAttribute("aria-busy", String(busy));
  document.querySelectorAll("#chat-form input, #chat-form button, #agent").forEach((control) => {
    control.disabled = busy;
  });
  document.querySelectorAll("#demo-prompts button, #transactions button[data-eligible]").forEach((control) => {
    control.disabled = busy;
  });
}

async function postChat(payload) {
  if (isBusy()) return;
  // A new turn closes any open confirmation and any open list of candidates:
  // an old "Confirmar" or an old chip must not fire.
  document.querySelectorAll(".chat-confirm button, .chat-candidates .candidate").forEach((button) => {
    if (!button.closest("#demo-prompts")) button.disabled = true;
  });
  threadLog.forEach((entry) => {
    entry.closed = true;
  });
  const typing = el("div", "msg msg-audit", t("typingLabel"));
  typingNode = typing;
  setBusy(true);
  document.getElementById("thread").append(typing);
  scrollToEnd();
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
    typingNode = null;
    setBusy(false);
    const input = document.getElementById("chat-input");
    if (!document.getElementById("view-chat").hidden) input.focus({ preventScroll: true });
  }
}

function selectCandidate(candidate) {
  if (isBusy()) return;
  logEntry({ type: "charge", candidate });
  postChat({ selected_reference: candidate.reference });
}

function renderCandidates(box, candidates, closed = false) {
  const chips = el("div", "chat-candidates");
  (candidates || []).forEach((candidate) => {
    const chip = el("button", "candidate", humanStatement(candidate));
    chip.type = "button";
    if (closed) {
      chip.disabled = true;
    } else if (!candidate.eligible) {
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
const STEP_PAUSE_MS = 500;
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
  // No staging when nobody can watch it: reduced motion, or the panel is a
  // closed drawer on a phone. Then the answer shows at once.
  const visible = list.offsetParent !== null;
  const staged = animate && visible && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
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

/* Information card of a closed charge: its state, why it is closed and the
   verified facts the server sends (the case, or the window and its last day).
   The page computes no date: every value comes from the listing. */
function chargeInfoCard(tx) {
  const state = tx.case_state || "not_disputable";
  const card = el("div", "msg msg-audit charge-info");
  card.setAttribute("data-testid", "charge-info");
  const head = el("div", "handoff-head");
  head.append(el("span", `pill pill-${STATE_TONES[state] || "neutral"}`, stateLabel(tx)));
  if (tx.merchant) head.append(el("strong", "", tx.merchant));
  card.append(head);
  if (tx.merchant && tx.amount) card.append(el("p", "", receiptCharge(tx)));
  const text = strings[`chargeInfo.${state}`];
  if (text) card.append(el("p", "", fillTemplate(text, tx)));
  const grid = el("div", "card-grid");
  if (tx.case_id) grid.append(cardField("field_reference", tx.case_id));
  if (state === "not_disputable" && tx.status) grid.append(cardField("chargeInfoStatus", statusLabel(tx.status)));
  if (tx.window_days) grid.append(cardField("chargeInfoWindow", fill(t("chargeInfoDays"), { days: tx.window_days })));
  if (tx.last_eligible_date) grid.append(cardField("whyLastDay", formatDate(tx.last_eligible_date)));
  if (grid.childElementCount) card.append(grid);
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
    renderCandidates(box, body.candidates, Boolean(entry && entry.closed));
    thread.append(box);
  } else if (body.kind === "handoff") {
    // Say what happened first, in plain words, then show the detail card.
    // The ticket number (HO-…) is customer-facing, like under field_reference.
    const ticket = fill(t("handoffLead"), { reference: body.reference });
    const lead = el("div", "msg msg-bot", [ticket, t(body.reason_key), t("handoffNext")].join(" "));
    lead.setAttribute("data-testid", "handoff-lead");
    thread.append(lead);
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
    // A closed charge cannot start a dispute, but a tap still tells the customer
    // why: an information card in the thread, with no turn sent to the chat.
    item.classList.add("tx-closed");
    const reason = t(tx.ineligibleKey || "candidateOutOfWindow");
    item.title = reason;
    item.append(el("span", "chat-sub tx-reason", reason));
    item.addEventListener("click", () => {
      closeDrawers();
      logEntry({ type: "info", tx });
    });
  } else {
    item.setAttribute("data-eligible", "");
    item.disabled = isBusy();
    item.addEventListener("click", () => {
      closeDrawers();
      selectCandidate(tx);
    });
  }
  return item;
}

/* The header line of a session: the masked product when the data has one,
   then country and language. Without a product the line has no type and no digits. */
/* Who this session is, for the header. A demo persona shows its name; a
   password login shows the user name the person typed. Nothing comes from the
   server, so no identifier reaches the page through the API. The label rides
   in the history entry, so a reload of the tab keeps it without any storage. */
const PERSONA_KEYS = {
  normal: "personaNormal",
  ambiguous: "personaAmbiguous",
  "high-amount": "personaHighAmount",
  "not-me": "personaNotMe",
};
let sessionLabel = null;

function sessionLabelText() {
  if (!sessionLabel) return "";
  if (sessionLabel.persona) return `${t("sessionDemo")}: ${t(PERSONA_KEYS[sessionLabel.persona] || "")}`;
  if (sessionLabel.user) return `${t("sessionUser")}: ${sessionLabel.user}`;
  return "";
}

function renderSessionContext(payload) {
  const parts = [];
  const who = sessionLabelText();
  if (who) parts.push(who);
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

/* "Mis reclamos": the cases of this customer, from the case store. The panel
   shows the five most recent and one control for the rest. The API still sends
   every case, so the page pages them itself and no request changes. */
const CASES_PAGE = 5;
let casesShowAll = false;

function casesShowAllButton(total) {
  const button = el("button", "theme-toggle cases-toggle", fill(t("casesShowAll"), { count: total }));
  button.type = "button";
  button.setAttribute("data-testid", "cases-show-all");
  button.addEventListener("click", () => {
    casesShowAll = true;
    if (lastTransactions) renderCases(lastTransactions.cases || []);
  });
  return button;
}

/* The charge behind a claim, from the listing; a claim with no charge (a
   handoff that named none) shows its own facts. */
function caseInfo(item) {
  const rows = (lastTransactions && lastTransactions.transactions) || [];
  const tx = rows.find((row) => row.case_id === item.case_id);
  return tx || { ...item, status: "" };
}

function renderCases(cases) {
  const box = document.getElementById("cases");
  box.textContent = "";
  if (!cases.length) {
    box.append(el("p", "chat-sub", t("casesEmpty")));
    return;
  }
  const shown = casesShowAll ? cases : cases.slice(0, CASES_PAGE);
  shown.forEach((item) => {
    // A claim opens the same information card as its charge in the list.
    const card = el("button", "candidate case-card");
    card.type = "button";
    card.setAttribute("data-testid", "case-card");
    card.addEventListener("click", () => {
      closeDrawers();
      logEntry({ type: "info", tx: caseInfo(item) });
    });
    const top = el("span", "tx-line");
    top.append(el("strong", "case-id", item.case_id));
    top.append(el("span", `pill pill-${STATE_TONES[item.case_state] || "neutral"}`, t(`state.${item.case_state}`)));
    card.append(top);
    const what = [item.merchant, item.amount ? formatAmount(item.amount, item.currency) : "", item.date ? formatDate(item.date) : ""];
    card.append(el("span", "chat-sub", what.filter(Boolean).join(" · ")));
    box.append(card);
  });
  if (!casesShowAll && cases.length > CASES_PAGE) {
    box.append(casesShowAllButton(cases.length));
  }
}

function paintCharges(payload) {
  lastTransactions = payload;
  renderCases(payload.cases || []);
  const box = document.getElementById("transactions");
  box.textContent = "";
  const rows = payload.transactions || [];
  if (!rows.length) {
    box.append(el("p", "chat-sub", t("txEmpty")));
    return;
  }
  rows.forEach((tx) => box.append(renderCharge(tx)));
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
  // The person chip never stands alone. An account without a charge and
  // without a repeated merchant has nothing to demo, so the page hides all
  // chips instead of offering one button that only opens a handoff ticket.
  if (prompts.length) prompts.push(t("demoPerson"));

  prompts.forEach((phrase) => {
    const chip = el("button", "candidate", phrase);
    chip.type = "button";
    chip.disabled = isBusy();
    chip.addEventListener("click", () => {
      if (isBusy()) return;
      addBubble(phrase);
      postChat({ message: phrase });
    });
    box.append(chip);
  });
  const showExamples = demoAvailable && prompts.length > 0;
  box.hidden = !showExamples;
  document.getElementById("demo-hint").hidden = !showExamples;
}

/* Advisor view: escalated tickets, newest first. The list shows why each case
   came (reason, country, language, age); the detail is read-only and adds the
   handoff package and the trace of the turn that filed it. On a wide screen the
   list and the detail sit side by side; on a phone the detail replaces the list. */
/* Country and language codes as words; an unknown code shows as it is. */
function countryName(code) {
  return strings[`country.${code}`] || code;
}

function languageName(code) {
  return strings[`lang.${code}`] || code;
}

let openCaseId = null;

function ticketRow(ticket) {
  const row = el("button", "candidate queue-row");
  row.type = "button";
  row.setAttribute("data-testid", "queue-row");
  row.setAttribute("data-case-id", ticket.case_id);
  if (ticket.case_id === openCaseId) row.setAttribute("aria-current", "true");
  const top = el("span", "tx-line");
  top.append(el("strong", "", ticket.case_id));
  top.append(el("span", "chat-sub", `${t("q_created")}: ${formatDate(ticket.created_at)}`));
  row.append(top);
  const reason = el("strong", "queue-reason", t(ticket.reason_key));
  reason.title = t("q_reason");
  row.append(reason);
  const tags = el("span", "queue-tags");
  const country = el("span", "pill pill-neutral", countryName(ticket.country));
  country.title = t("q_country");
  const language = el("span", "pill pill-neutral", languageName(ticket.package.language));
  language.title = t("q_language");
  tags.append(country, language);
  row.append(tags);
  row.addEventListener("click", () => navigate(`/queue/${encodeURIComponent(ticket.case_id)}`));
  return row;
}

/* The list repaints on its own while the advisor watches it, so a case filed
   in another tab shows up without a reload. The open detail stays as it is. */
const QUEUE_REFRESH_MS = 15000;
let queueTimer = null;

function stopQueueRefresh() {
  clearInterval(queueTimer);
  queueTimer = null;
}

async function loadQueue() {
  const response = await api("/api/v1/handoffs");
  if (!response.ok) return;
  const tickets = await response.json();
  const box = document.getElementById("queue");
  box.textContent = "";
  document.getElementById("queue-count").textContent = String(tickets.length);
  if (!tickets.length) box.append(el("p", "chat-sub", t("q_empty")));
  tickets.forEach((ticket) => box.append(ticketRow(ticket)));
  if (!queueTimer) queueTimer = setInterval(loadQueue, QUEUE_REFRESH_MS);
}

function showQueueList() {
  openCaseId = null;
  document.getElementById("view-queue").classList.remove("queue-open");
  const detail = document.getElementById("queue-detail");
  detail.textContent = "";
  detail.append(el("p", "chat-sub queue-placeholder", t("q_select")));
  document.querySelectorAll(".queue-row[aria-current]").forEach((row) => row.removeAttribute("aria-current"));
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
  // A table, one row per step: the columns line up, so the advisor compares steps.
  const wrap = el("div", "trace-wrap");
  const table = el("table", "metrics-table trace-table");
  const head = el("tr");
  ["q_step", "q_tool", "q_outcome", "q_latency", "q_model", "q_prompt", "q_cost", "q_policyVersion"].forEach((key) => {
    head.append(el("th", "", t(key)));
  });
  const thead = el("thead");
  thead.append(head);
  const tbody = el("tbody");
  trace.steps.forEach((step) => {
    const row = el("tr");
    [
      step.step,
      step.tool || "",
      step.outcome || "",
      Number(step.latency_ms).toFixed(1),
      step.model || "",
      step.prompt_version || "",
      Number(step.cost_usd).toFixed(4),
      step.policy_version || "",
    ].forEach((value) => row.append(el("td", "", value)));
    tbody.append(row);
  });
  table.append(thead, tbody);
  wrap.append(table);
  card.append(wrap);
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

/* The handoff as the system filed it, for the JSON tab. The screen never shows
   a customer identifier (decision 009), so the export leaves that field out too. */
function handoffExport(ticket, trace) {
  const shown = { ...ticket };
  delete shown["customer_id"];
  return { ticket: shown, trace };
}

function jsonBlock(caseId, data) {
  const box = el("div", "msg msg-audit json-block");
  const text = JSON.stringify(data, null, 2);
  const bar = el("div", "json-bar");
  const copy = el("button", "theme-toggle", t("q_copy"));
  copy.type = "button";
  copy.setAttribute("data-testid", "json-copy");
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      copy.textContent = t("q_copied");
    } catch (error) {
      copy.textContent = t("q_copyFailed");
    }
    setTimeout(() => {
      copy.textContent = t("q_copy");
    }, 1500);
  });
  const download = el("a", "theme-toggle", t("q_download"));
  download.href = URL.createObjectURL(new Blob([text], { type: "application/json" }));
  download.download = `${caseId}.json`;
  download.setAttribute("data-testid", "json-download");
  bar.append(copy, download);
  box.append(el("p", "chat-sub", t("q_jsonNote")), bar);
  const pre = el("pre", "json-view", text);
  pre.setAttribute("data-testid", "json-view");
  pre.tabIndex = 0;
  box.append(pre);
  return box;
}

/* Three tabs: the summary for a person, the trace and the raw JSON. */
const DETAIL_TABS = ["summary", "trace", "json"];
let detailTab = "summary";

function detailTabs(panels) {
  const wrap = el("div", "detail-tabs");
  const list = el("div", "tab-list");
  list.setAttribute("role", "tablist");
  const buttons = DETAIL_TABS.map((name) => {
    const button = el("button", "theme-toggle tab", t(`q_tab.${name}`));
    button.type = "button";
    button.id = `tab-${name}`;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-controls", `panel-${name}`);
    button.setAttribute("data-testid", `tab-${name}`);
    list.append(button);
    return button;
  });
  const select = (name) => {
    detailTab = name;
    DETAIL_TABS.forEach((other, index) => {
      const on = other === name;
      buttons[index].setAttribute("aria-selected", String(on));
      buttons[index].tabIndex = on ? 0 : -1;
      panels[other].hidden = !on;
    });
  };
  buttons.forEach((button, index) => {
    button.addEventListener("click", () => select(DETAIL_TABS[index]));
    button.addEventListener("keydown", (event) => {
      const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      const next = (index + step + DETAIL_TABS.length) % DETAIL_TABS.length;
      select(DETAIL_TABS[next]);
      buttons[next].focus();
    });
  });
  wrap.append(list);
  DETAIL_TABS.forEach((name) => {
    panels[name].id = `panel-${name}`;
    panels[name].setAttribute("role", "tabpanel");
    panels[name].setAttribute("aria-labelledby", `tab-${name}`);
    wrap.append(panels[name]);
  });
  select(detailTab);
  return wrap;
}

async function openTicket(caseId) {
  const detail = document.getElementById("queue-detail");
  const [response, traceResponse] = await Promise.all([
    api(`/api/v1/handoffs/${encodeURIComponent(caseId)}`),
    api(`/api/v1/handoffs/${encodeURIComponent(caseId)}/trace`),
  ]);
  if (!response.ok) {
    showQueueList();
    detail.textContent = "";
    detail.append(el("p", "chat-sub queue-placeholder", t("q_notFound")));
    return;
  }
  const ticket = await response.json();
  const trace = traceResponse.ok ? await traceResponse.json() : { available: false, steps: [] };
  openCaseId = ticket.case_id;
  document.querySelectorAll(".queue-row").forEach((row) => {
    if (row.getAttribute("data-case-id") === openCaseId) row.setAttribute("aria-current", "true");
    else row.removeAttribute("aria-current");
  });
  detail.textContent = "";
  const back = el("button", "theme-toggle queue-back", t("q_back"));
  back.type = "button";
  back.setAttribute("data-testid", "queue-back");
  back.addEventListener("click", () => navigate("/queue"));
  detail.append(back);
  detail.append(el("h3", "chat-title", `${ticket.case_id} · ${codeLabel("ticketStatus", ticket.status) || ticket.status}`));
  // No customer identifier on the screen: the advisor gets facts, not an id.
  const summary = el("div", "");
  summary.append(field("q_country", `${countryName(ticket.country)} · ${t("q_language")}: ${languageName(ticket.package.language)}`));
  summary.append(field("q_reason", t(ticket.reason_key)));
  summary.append(packageBlock(ticket.package));
  const traceTab = el("div", "");
  traceTab.append(traceBlock(trace));
  const jsonTab = el("div", "");
  jsonTab.append(jsonBlock(ticket.case_id, handoffExport(ticket, trace)));
  detail.append(detailTabs({ summary, trace: traceTab, json: jsonTab }));
  document.getElementById("view-queue").classList.add("queue-open");
}

/* Navigation: the view lives in the URL hash, so a reload keeps it, the Back
   button works and an advisor can share the link of a case.
     #/          entry (login)
     #/chat      the customer chat
     #/queue     the advisor list
     #/queue/ID  the advisor list with one case open */
let sessionRole = null;

function currentRoute() {
  const path = location.hash.replace(/^#/, "") || "/";
  const match = path.match(/^\/queue\/(.+)$/);
  if (match) return { view: "queue", caseId: decodeURIComponent(match[1]) };
  if (path === "/queue") return { view: "queue", caseId: null };
  if (path === "/chat") return { view: "chat", caseId: null };
  return { view: "login", caseId: null };
}

/* A new entry in the history: the Back button returns here. */
function navigate(path) {
  if (location.hash === `#${path}`) applyRoute();
  else location.hash = path;
}

/* Same entry, new URL: for the moves the Back button must not undo (login, logout). */
function replaceRoute(path) {
  history.replaceState(sessionLabel ? { sessionLabel } : null, "", `#${path}`);
}

async function applyRoute() {
  const route = currentRoute();
  if (sessionRole === "advisor") {
    if (route.view !== "queue") {
      replaceRoute("/queue");
      return applyRoute();
    }
    if (document.getElementById("view-queue").hidden) {
      show("view-queue");
      await loadQueue();
    }
    if (route.caseId) await openTicket(route.caseId);
    else showQueueList();
  } else if (sessionRole === "customer") {
    if (route.view !== "chat") replaceRoute("/chat");
  }
}

window.addEventListener("hashchange", applyRoute);
document.getElementById("queue-refresh").addEventListener("click", loadQueue);

async function enterSession(role) {
  sessionRole = role;
  if (role === "advisor") {
    // A shared case link opened before the login stays the target.
    if (currentRoute().view !== "queue") replaceRoute("/queue");
    await applyRoute();
    return;
  }
  replaceRoute("/chat");
  startThread();
  show("view-chat");
  await loadContext();
  await loadTransactions();
}

/* A reload with a live session goes back to the same view, not to the login. */
async function resumeSession() {
  const response = await fetch("/api/v1/auth/me");
  if (!response.ok) {
    if (currentRoute().view === "chat") replaceRoute("/");
    return;
  }
  const me = await response.json();
  sessionLabel = (history.state && history.state.sessionLabel) || null;
  await enterSession(me.role);
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
  sessionLabel = role === "customer" ? { user: document.getElementById("login-user").value.trim() } : null;
  resetPassword();
  await enterSession(role);
});

function resetPassword() {
  const field = document.getElementById("login-pass");
  field.value = "";
  field.type = "password";
  const button = document.getElementById("toggle-pass");
  button.setAttribute("aria-pressed", "false");
  button.setAttribute("data-i18n", "showPassword");
  button.textContent = t("showPassword");
}

/* Show or hide the password: the field changes type, the button says what it does next. */
document.getElementById("toggle-pass").addEventListener("click", (event) => {
  const field = document.getElementById("login-pass");
  const show = field.type === "password";
  field.type = show ? "text" : "password";
  event.currentTarget.setAttribute("aria-pressed", String(show));
  event.currentTarget.setAttribute("data-i18n", show ? "hidePassword" : "showPassword");
  event.currentTarget.textContent = t(show ? "hidePassword" : "showPassword");
  field.focus();
});

document.getElementById("chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const value = input.value.trim();
  if (!value || isBusy()) return;
  addBubble(value);
  postChat({ message: value });
  input.value = "";
});

document.getElementById("agent").addEventListener("click", () => {
  if (isBusy()) return;
  const message = t("agentMessage");
  addBubble(t("agentButton"));
  postChat({ message });
});

document.getElementById("logout").addEventListener("click", async () => {
  await fetch("/api/v1/auth/logout", { method: "POST" });
  clearThread();
  show("view-login");
  document.getElementById("login-error").textContent = "";
  resetPassword();
  sessionRole = null;
  sessionLabel = null;
  replaceRoute("/");
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
  demoAvailable = available;
  document.getElementById("demo-personas").hidden = !available;
  // The password form stays visible with or without the personas.
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
  sessionRole = "customer";
  sessionLabel = { persona };
  replaceRoute("/chat");
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

loadLocale("es-419").then(resumeSession);
loadBrand();
loadDemoEntry();
loadDataNotice();
loadBuildInfo();
