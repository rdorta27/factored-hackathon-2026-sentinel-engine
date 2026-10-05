(function () {
  // The language of the page follows the address (?lang=en), then the last choice, then the browser.
  var KEY = "sentinel-lang";
  var NAMES = { en: "en", es: "es-419", "es-419": "es-419", pt: "pt-br", "pt-br": "pt-br" };
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function go(lang) {
    var alt = document.querySelector('link[rel="alternate"][data-lang="' + lang + '"]');
    if (alt) { location.replace(alt.href + location.hash); }
  }
  var html = document.documentElement.lang;
  var here = html.indexOf("es") === 0 ? "es-419" : html === "pt-BR" ? "pt-br" : "en";
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-lang]");
    if (a) { set(a.getAttribute("data-lang")); }
  });
  var q = /[?&]lang=([\w-]+)/.exec(location.search);
  var asked = q ? NAMES[q[1].toLowerCase()] : null;
  if (asked) {
    set(asked);
    if (asked !== here) { go(asked); }
    return;
  }
  if (here !== "en") { return; }
  var want = get();
  if (!want) {
    var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"];
    for (var i = 0; i < list.length; i++) {
      var p = String(list[i]).toLowerCase().split("-")[0];
      if (p === "es") { want = "es-419"; break; }
      if (p === "pt") { want = "pt-br"; break; }
      if (p === "en") { want = "en"; break; }
    }
  }
  if (want && want !== "en") { go(want); }
})();
