(function () {
  var root = document.documentElement;
  root.classList.add("js");
  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
  var i = 0;
  function fit() {
    var s = Math.min(window.innerWidth / 1280, (window.innerHeight - 64) / 720);
    root.style.setProperty("--s", String(s));
  }
  function show(n) {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach(function (el, k) { el.classList.toggle("on", k === i); });
    try { history.replaceState(null, "", "#" + (i + 1)); } catch (e) {}
    document.getElementById("pos").textContent = (i + 1) + " / " + slides.length;
  }
  document.getElementById("prev").addEventListener("click", function () { show(i - 1); });
  document.getElementById("next").addEventListener("click", function () { show(i + 1); });
  document.addEventListener("keydown", function (e) {
    if (e.target.closest && e.target.closest("a,button") && e.key === "Enter") { return; }
    if (["ArrowRight", "PageDown", " "].indexOf(e.key) >= 0) { e.preventDefault(); show(i + 1); }
    else if (["ArrowLeft", "PageUp"].indexOf(e.key) >= 0) { e.preventDefault(); show(i - 1); }
    else if (e.key === "Home") { show(0); }
    else if (e.key === "End") { show(slides.length - 1); }
    else if (e.key === "f") { if (document.fullscreenElement) { document.exitFullscreen(); } else { root.requestFullscreen && root.requestFullscreen(); } }
  });
  var x0 = null;
  document.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
  document.addEventListener("touchend", function (e) {
    if (x0 === null) { return; }
    var dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) { show(i + (dx < 0 ? 1 : -1)); }
    x0 = null;
  });
  window.addEventListener("resize", fit);
  fit();
  show((parseInt(location.hash.slice(1), 10) || 1) - 1);
})();
