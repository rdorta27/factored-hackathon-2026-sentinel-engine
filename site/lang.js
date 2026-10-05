(function () {
  // The language of the page follows the browser on the first visit, then the last choice.
  var KEY = "sentinel-lang";
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  var html = document.documentElement.lang;
  var here = html === "es" ? "es-la" : html === "pt-BR" ? "pt-br" : "en";
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-lang]");
    if (a) { set(a.getAttribute("data-lang")); }
  });
  if (here !== "en") { return; }
  var want = get();
  if (!want) {
    var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"];
    for (var i = 0; i < list.length; i++) {
      var p = String(list[i]).toLowerCase().split("-")[0];
      if (p === "es") { want = "es-la"; break; }
      if (p === "pt") { want = "pt-br"; break; }
      if (p === "en") { want = "en"; break; }
    }
  }
  if (want && want !== "en") {
    var alt = document.querySelector('link[rel="alternate"][data-lang="' + want + '"]');
    if (alt) { location.replace(alt.href + location.hash); }
  }
})();
