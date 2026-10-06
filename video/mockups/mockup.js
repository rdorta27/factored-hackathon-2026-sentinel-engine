// Shared player for the video mockups.
// - Scales the 1920x1080 stage to the window.
// - [data-at="ms"] gets the class "in" at that time. [data-out="ms"] gets "out".
// - [data-type="ms"] types its text from that time. [data-count="ms"] counts up to data-to.
// - [data-class="ms:name"] adds a class at that time (for example "alert" or "tap").
// Keys: R or click replays, H hides the hint, F goes full screen.
(function () {
  var stage = document.querySelector(".stage");
  function fit() {
    var s = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    stage.style.transform = "scale(" + s + ")";
  }
  window.addEventListener("resize", fit);
  fit();

  var timers = [];
  var typed = Array.prototype.map.call(document.querySelectorAll("[data-type]"), function (el) {
    return { el: el, text: el.textContent };
  });

  function at(ms, fn) { timers.push(setTimeout(fn, ms)); }

  function reset() {
    timers.forEach(clearTimeout);
    timers = [];
    document.querySelectorAll("[data-at]").forEach(function (el) { el.classList.remove("in", "out"); });
    document.querySelectorAll("[data-class]").forEach(function (el) {
      el.getAttribute("data-class").split(" ").forEach(function (pair) { el.classList.remove(pair.split(":")[1]); });
    });
    typed.forEach(function (t) { t.el.textContent = ""; });
    document.querySelectorAll("[data-count]").forEach(function (el) { el.textContent = el.getAttribute("data-from") || "0"; });
  }

  function play() {
    reset();
    document.querySelectorAll("[data-at]").forEach(function (el) {
      at(+el.getAttribute("data-at"), function () { el.classList.add("in"); });
      if (el.hasAttribute("data-out")) { at(+el.getAttribute("data-out"), function () { el.classList.add("out"); }); }
    });
    document.querySelectorAll("[data-class]").forEach(function (el) {
      el.getAttribute("data-class").split(" ").forEach(function (pair) {
        var p = pair.split(":");
        at(+p[0], function () { el.classList.remove(p[1]); void el.offsetWidth; el.classList.add(p[1]); });
      });
    });
    typed.forEach(function (t) {
      var start = +t.el.getAttribute("data-type");
      var speed = +(t.el.getAttribute("data-speed") || 34);
      for (var i = 1; i <= t.text.length; i++) {
        (function (n) { at(start + n * speed, function () { t.el.textContent = t.text.slice(0, n); }); })(i);
      }
    });
    document.querySelectorAll("[data-count]").forEach(function (el) {
      var start = +el.getAttribute("data-count");
      var from = +(el.getAttribute("data-from") || 0);
      var to = +el.getAttribute("data-to");
      var dur = +(el.getAttribute("data-dur") || 1600);
      var dec = +(el.getAttribute("data-dec") || 0);
      var suffix = el.getAttribute("data-suffix") || "";
      var steps = 40;
      for (var i = 1; i <= steps; i++) {
        (function (k) {
          at(start + (dur * k) / steps, function () {
            var e = 1 - Math.pow(1 - k / steps, 3);
            var v = from + (to - from) * e;
            el.textContent = v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suffix;
          });
        })(i);
      }
    });
  }

  var hint = document.createElement("div");
  hint.className = "hint";
  hint.textContent = "R or click: replay · H: hide this · F: full screen";
  document.body.appendChild(hint);

  document.addEventListener("click", play);
  document.addEventListener("keydown", function (e) {
    var k = e.key.toLowerCase();
    if (k === "r") { play(); }
    if (k === "h") { hint.classList.toggle("off"); }
    if (k === "f") { document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); }
  });
  play();
})();
