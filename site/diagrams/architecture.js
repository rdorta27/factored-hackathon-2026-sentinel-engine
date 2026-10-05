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
  var notes = { demo: note.dataset.noteDemo, prod: note.dataset.noteProd };

  function fit(svg) {
    // Squeeze a label that is wider than its node. English never needs it; Spanish and Portuguese may.
    svg.querySelectorAll("g.node").forEach(function (g) {
      var box = g.querySelector("rect.box");
      if (!box) { return; }
      var w = box.getBBox().width, chip = g.querySelector("circle.chip");
      var chipLeft = chip ? parseFloat(chip.getAttribute("cx")) - parseFloat(chip.getAttribute("r")) : w;
      g.querySelectorAll("text").forEach(function (t) {
        if (t.classList.contains("chipt")) { return; }
        t.removeAttribute("textLength");
        t.removeAttribute("lengthAdjust");
        var x = parseFloat(t.getAttribute("x")) || 0;
        var avail = (t.classList.contains("t1") ? chipLeft - 4 : w - 8) - x;
        if (t.getComputedTextLength() > avail) {
          t.setAttribute("textLength", avail.toFixed(1));
          t.setAttribute("lengthAdjust", "spacingAndGlyphs");
        }
      });
    });
  }

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
    fit(svg);
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
  fit(svg);
})();
