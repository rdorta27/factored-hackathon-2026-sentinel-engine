(function () {
  document.documentElement.classList.add("js");
  var chips = Array.prototype.slice.call(document.querySelectorAll("[data-go]"));
  var steps = document.querySelectorAll(".tstep");
  var ids = chips.map(function (c) { return c.dataset.go; });
  var cur = 0;
  function go(i) {
    cur = Math.max(0, Math.min(ids.length - 1, i));
    chips.forEach(function (c, k) { c.classList.toggle("on", k === cur); c.setAttribute("aria-current", k === cur ? "step" : "false"); });
    steps.forEach(function (s) { s.classList.toggle("on", s.dataset.step === ids[cur]); });
    document.getElementById("prev").disabled = cur === 0;
    document.getElementById("next").disabled = cur === ids.length - 1;
    try { history.replaceState(null, "", "#" + ids[cur]); } catch (e) {}
  }
  chips.forEach(function (c, k) { c.addEventListener("click", function () { go(k); }); });
  document.getElementById("prev").addEventListener("click", function () { go(cur - 1); });
  document.getElementById("next").addEventListener("click", function () { go(cur + 1); });
  var quotes = document.querySelectorAll(".sample");
  function sample(id) { quotes.forEach(function (q) { q.classList.toggle("on", q.dataset.sample === id); }); }
  document.querySelectorAll("input[name=sample]").forEach(function (r) { r.addEventListener("change", function () { sample(r.value); }); });
  sample(document.querySelector("input[name=sample]:checked").value);
  var start = ids.indexOf(location.hash.slice(1));
  go(start >= 0 ? start : 0);
})();
