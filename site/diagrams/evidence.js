(function () {
  document.documentElement.classList.add("js");
  var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-tab]"));
  var panels = document.querySelectorAll(".series");
  function show(id) {
    tabs.forEach(function (t) {
      var on = t.dataset.tab === id;
      t.classList.toggle("on", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
    });
    panels.forEach(function (p) { p.classList.toggle("on", p.dataset.series === id); });
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }
  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { show(t.dataset.tab); });
    t.addEventListener("keydown", function (e) {
      var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : -1;
      if (j >= 0) { j = (j + tabs.length) % tabs.length; tabs[j].focus(); show(tabs[j].dataset.tab); e.preventDefault(); }
    });
  });
  var ids = tabs.map(function (t) { return t.dataset.tab; });
  var start = location.hash.slice(1);
  show(ids.indexOf(start) >= 0 ? start : ids[0]);
})();
