(function () {
  var root = document.documentElement;
  root.classList.add("js");
  var svg = document.getElementById("arch");
  var nodes = svg.querySelectorAll(".node");
  var picks = document.querySelectorAll("[data-pick]");
  var details = document.querySelectorAll(".detail");
  var hint = document.querySelector(".pick-hint");
  var segs = document.querySelectorAll("[data-view]");
  var note = document.getElementById("view-note");
  var notes = {
    demo: "The demo view shows what runs on the public link.",
    prod: "The production view shows what replaces each part. A thick border marks a part that changes."
  };

  function select(id, focus) {
    nodes.forEach(function (n) { n.classList.toggle("sel", n.dataset.node === id); });
    picks.forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.pick === id ? "true" : "false"); });
    details.forEach(function (d) { d.classList.toggle("on", d.dataset["for"] === id); });
    hint.classList.add("off");
    if (focus) { document.getElementById("d-" + id).scrollIntoView({ block: "nearest" }); }
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }

  function view(name) {
    var prod = name === "prod";
    segs.forEach(function (s) {
      var on = s.dataset.view === name;
      s.classList.toggle("on", on);
      s.setAttribute("aria-pressed", on ? "true" : "false");
    });
    nodes.forEach(function (n) {
      n.classList.toggle("prod", prod);
      n.classList.toggle("real", !prod && n.dataset.status === "real");
      n.classList.toggle("mock", !prod && n.dataset.status === "mock");
      var key = prod ? "prod" : "demo";
      n.querySelectorAll("text[data-demo]").forEach(function (t) { t.textContent = t.dataset[key]; });
    });
    note.textContent = notes[name];
  }

  nodes.forEach(function (n) {
    n.addEventListener("click", function () { select(n.dataset.node, true); });
    n.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(n.dataset.node, true); }
    });
  });
  picks.forEach(function (b) { b.addEventListener("click", function () { select(b.dataset.pick, true); }); });
  segs.forEach(function (s) { s.addEventListener("click", function () { view(s.dataset.view); }); });

  var start = location.hash.slice(1);
  if (start && document.getElementById("d-" + start)) { select(start, false); }
})();
