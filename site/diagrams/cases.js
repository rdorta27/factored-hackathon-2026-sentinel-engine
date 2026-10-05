(function () {
  document.documentElement.classList.add("js");
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

  var routes = JSON.parse(document.getElementById("routes").textContent);
  var svg = document.getElementById("map");
  var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-tab]"));
  var panels = document.querySelectorAll(".case");

  function show(id) {
    var lit = routes[id];
    svg.classList.add("focus");
    svg.querySelectorAll(".node").forEach(function (n) { n.classList.toggle("lit", lit.indexOf(n.dataset.node) >= 0); });
    svg.querySelectorAll("[data-e]").forEach(function (e) {
      var p = e.dataset.e.split(":");
      e.classList.toggle("lit", lit.indexOf(p[0]) >= 0 && lit.indexOf(p[1]) >= 0 && lit.indexOf(p[1]) === lit.indexOf(p[0]) + 1);
    });
    tabs.forEach(function (t) {
      var on = t.dataset.tab === id;
      t.classList.toggle("on", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
    });
    panels.forEach(function (p) { p.classList.toggle("on", p.dataset["case"] === id); });
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }

  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { show(t.dataset.tab); });
    t.addEventListener("keydown", function (e) {
      var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : -1;
      if (j >= 0) { j = (j + tabs.length) % tabs.length; tabs[j].focus(); show(tabs[j].dataset.tab); e.preventDefault(); }
    });
  });
  var start = location.hash.slice(1);
  show(routes[start] ? start : tabs[0].dataset.tab);
  fit(svg);
})();
