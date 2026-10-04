// Copy button for the "Prompt Box" content block (.cb-prompt).
// The text lives in the <pre>, so it stays readable without this script.
document.addEventListener("click", function (e) {
  var btn = e.target.closest(".cb-copy");
  if (!btn) return;
  var box = btn.closest(".cb-prompt");
  var pre = box && box.querySelector("pre");
  if (!pre) return;

  var done = function () {
    var old = btn.getAttribute("data-label") || btn.textContent;
    btn.setAttribute("data-label", old);
    btn.textContent = "Copied";
    setTimeout(function () { btn.textContent = old; }, 1800);
  };

  // Older route: select the text and use the browser's copy command.
  var fallback = function () {
    var range = document.createRange();
    range.selectNodeContents(pre);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) {}
    if (ok) {
      done();
      sel.removeAllRanges();
    }
    // If copying is blocked, the text stays selected so the reader can press Ctrl+C.
  };

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(pre.innerText).then(done, fallback);
  } else {
    fallback();
  }
});
