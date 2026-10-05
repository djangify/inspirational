/* Djangify Content Blocks Premium: interactive blocks (content-blocks-premium.js)

   One file, no setup. Add it once to every page that shows your articles:
     <script src="content-blocks-premium.js" defer></script>
   Your posts then contain plain HTML with data-cbp attributes. This script finds the blocks,
   adds the checkboxes, text boxes and buttons, and saves each reader's progress in their own
   browser (localStorage). Nothing is sent anywhere. The styles are built in and follow your
   theme shades (--color-primary and friends) when your site defines them.

   Blocks: stats, checklist, guide, reflect, score, quiz, switch.
   Without this script every block still reads as a normal list or box.

   Copyright Djangify. Licensed for use on your own and your clients' sites. See LICENSE.md.
   Do not resell or redistribute this file. */
(function () {
  "use strict";
  if (window.cbpLoaded) { return; }
  window.cbpLoaded = true;

  var CSS = [
    ".cbp{--cbp-p:var(--color-primary,#365272);--cbp-pc:var(--color-primary-contrast,#fff);--cbp-a:var(--color-accent,#b85c3b);--cbp-ac:var(--color-accent-contrast,#fff);--cbp-s:var(--color-secondary,#d6c6b3);--cbp-sc:var(--color-secondary-contrast,#1a1a1a);--cbp-l:var(--color-light,#f8fafc);--cbp-bd:#e2e8f0;--cbp-ok:#cdf0dd;--cbp-okb:#1f9d62;--cbp-t1:#f6f8fb;--cbp-t2:#fdf6f2;--cbp-t3:#f9f5ef;--cbp-t4:#f3f7ff;",
    "font-family:var(--cbp-font,inherit);font-size:var(--cbp-size,1.125rem);color:#1b2230;background:var(--cbp-l);border:1px solid var(--cbp-bd);border-top:4px solid var(--cbp-p);border-radius:.75rem;padding:1.25rem 1.5rem;margin:1.5rem 0;line-height:1.6;box-sizing:border-box}",
    /* light backgrounds that follow the site's own colors where the browser can mix them */
    "@supports (color:color-mix(in srgb,red 50%,white)){.cbp{--cbp-t1:color-mix(in srgb,var(--cbp-p) 5%,#fff);--cbp-t2:color-mix(in srgb,var(--cbp-a) 6%,#fff);--cbp-t3:color-mix(in srgb,var(--cbp-s) 14%,#fff);--cbp-t4:color-mix(in srgb,var(--cbp-p) 6%,#fff)}}",
    ".cbp-checklist{background:#fff}",
    ".cbp-guide{background:#fff;border-top-color:var(--cbp-a)}",
    ".cbp-reflect{background:var(--cbp-t2);border-top-color:var(--cbp-a)}",
    ".cbp-score{background:var(--cbp-t4)}",
    ".cbp-switch{background:#fff}",
    ".cbp-quiz{background:var(--cbp-p);color:var(--cbp-pc);border-color:var(--cbp-p)}",
    ".cbp-quiz .cbp-label,.cbp-quiz h3,.cbp-quiz>ol>li>strong{color:inherit}",
    ".cbp-quiz [data-outcomes]>div{color:#1b2230}",
    ".cbp-quiz .cbp-actions button.cbp-quiet{border-color:rgba(255,255,255,.65);color:inherit}",
    ".cbp-quiz .cbp-actions button.cbp-quiet:hover{border-color:var(--cbp-s);color:var(--cbp-sc)}",
    ".cbp *{box-sizing:border-box}",
    ".cbp h3,.cbp h4{margin-top:0;font-weight:700;line-height:1.3}",
    ".cbp h3{font-size:1.1em}",
    ".cbp h4{font-size:1.05em}",
    ".cbp ul,.cbp ol{list-style:none;padding:0;margin:0}",
    ".cbp li{margin:0}",
    ".cbp .cbp-label,.cbp>span:first-child.cbp-label{display:block;margin-bottom:.5rem;font-size:.8em;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--cbp-p)}",
    ".cbp p{margin:.5rem 0}",
    /* buttons */
    ".cbp button.cbp-b,.cbp a.cbp-btn{display:inline-block;padding:.6rem 1.1rem;border:1px solid var(--cbp-a);border-radius:.375rem;background:var(--cbp-a);color:var(--cbp-ac);font:inherit;font-size:.95em;font-weight:600;line-height:1.3;text-decoration:none;cursor:pointer;transition:background-color .15s ease,color .15s ease}",
    ".cbp button.cbp-b:hover,.cbp a.cbp-btn:hover{background:var(--cbp-s);border-color:var(--cbp-s);color:var(--cbp-sc);text-decoration:none}",
    ".cbp button.cbp-b.cbp-quiet{background:transparent;border-color:#94a3b8;color:inherit}",
    ".cbp button.cbp-b.cbp-quiet:hover{background:var(--cbp-s);border-color:var(--cbp-s);color:var(--cbp-sc)}",
    ".cbp button:focus-visible,.cbp textarea:focus-visible,.cbp a:focus-visible,.cbp input:focus-visible+span,.cbp input:focus-visible{outline:3px solid var(--cbp-p);outline-offset:2px}",
    ".cbp-actions{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1rem}",
    /* progress */
    ".cbp-progress{margin:.25rem 0 1rem}",
    ".cbp-count{display:block;margin-bottom:.35rem;font-size:.9em;font-weight:600}",
    ".cbp-track{height:.6rem;border-radius:9999px;background:#e2e8f0;overflow:hidden}",
    ".cbp-fill{height:100%;width:0;background:var(--cbp-p);border-radius:9999px;transition:width .25s ease}",
    ".cbp-msg{margin:1rem 0 0;padding:.75rem 1rem;border-left:4px solid var(--cbp-p);border-radius:0 .5rem .5rem 0;background:#fff;font-weight:600}",
    ".cbp-msg:empty{display:none}",
    /* checklist */
    ".cbp-checklist>ul>li{margin:0 0 .6rem}",
    ".cbp-item{display:flex;gap:.8rem;align-items:flex-start;padding:.85rem 1rem;border:1px solid var(--cbp-bd);border-radius:.6rem;background:#fff;cursor:pointer;transition:background-color .2s ease,border-color .2s ease}",
    ".cbp-item input{flex:none;width:1.4rem;height:1.4rem;margin:.15rem 0 0;accent-color:var(--cbp-okb);cursor:pointer}",
    ".cbp-item-text strong,.cbp-item-text span{display:block}",
    ".cbp-item-text span{font-size:.9em;opacity:.85}",
    ".cbp li.cbp-is-done>.cbp-item{background:var(--cbp-ok);border-color:var(--cbp-okb)}",
    /* guide */
    ".cbp-guide>.cbp-progress{position:sticky;top:var(--cbp-top,0);z-index:5;margin:0 -1.5rem 1rem;padding:.6rem 1.5rem;background:#fff;border-bottom:1px solid var(--cbp-bd)}",
    ".cbp-guide>ol{counter-reset:cbpstep}",
    ".cbp-guide>ol>li{counter-increment:cbpstep;position:relative;margin:0 0 1rem;padding:1rem 1.25rem 1rem 4rem;background:#fff;border:1px solid var(--cbp-bd);border-radius:.75rem;scroll-margin-top:calc(var(--cbp-top,0px) + 5rem)}",
    ".cbp-guide>ol>li::before{content:counter(cbpstep);position:absolute;left:1rem;top:1rem;width:2.25rem;height:2.25rem;border-radius:9999px;background:var(--cbp-p);color:var(--cbp-pc);font-weight:700;display:flex;align-items:center;justify-content:center}",
    ".cbp-guide>ol>li.cbp-current{border-color:var(--cbp-a);box-shadow:0 0 0 2px var(--cbp-a)}",
    ".cbp-guide>ol>li{transition:background-color .2s ease,border-color .2s ease}",
    ".cbp-guide>ol>li.cbp-is-done{background:var(--cbp-ok);border-color:var(--cbp-okb)}",
    ".cbp-guide>ol>li.cbp-is-done::before{background:var(--cbp-okb);color:#fff}",
    ".cbp-guide>ol>li.cbp-is-done.cbp-current{box-shadow:none}",
    ".cbp-donebox input{accent-color:var(--cbp-okb)}",
    ".cbp-guide>ol>li>strong{display:block;font-size:1.05em}",
    ".cbp-guide>ol>li>span{display:block;font-size:.9em}",
    ".cbp-guide details{margin:.75rem 0 0;border:1px solid var(--cbp-bd);border-radius:.5rem;padding:0 .9rem}",
    ".cbp-guide summary{cursor:pointer;padding:.6rem 0;font-weight:600}",
    ".cbp-donebox{display:inline-flex;align-items:center;gap:.5rem;margin-top:.9rem;font-weight:600;cursor:pointer}",
    ".cbp-donebox input{width:1.3rem;height:1.3rem;accent-color:var(--cbp-p);cursor:pointer}",
    /* reflect */
    ".cbp-reflect>ol>li{padding:1rem 0;border-top:1px solid var(--cbp-bd)}",
    ".cbp-reflect>ol>li>strong{display:block;font-size:1em}",
    ".cbp-reflect>ol>li>span{display:block;font-size:.9em;opacity:.85}",
    ".cbp-reflect textarea{display:block;width:100%;min-height:6rem;margin-top:.6rem;padding:.7rem .85rem;border:1px solid #cbd5e1;border-radius:.5rem;background:#fff;color:#1b2230;font:inherit;line-height:1.5;resize:vertical}",
    ".cbp-saved{margin-top:.75rem;font-size:.85em;opacity:.8}",
    /* score */
    ".cbp-score>ol>li{padding:1rem 0;border-top:1px solid var(--cbp-bd)}",
    ".cbp-statement{display:block;font-weight:600;margin-bottom:.6rem}",
    ".cbp-rates{display:flex;flex-wrap:wrap;gap:.5rem}",
    ".cbp-rate{position:relative;display:inline-block}",
    ".cbp-rate input{position:absolute;opacity:0;width:100%;height:100%;margin:0;cursor:pointer}",
    ".cbp-rate span{display:flex;align-items:center;justify-content:center;min-width:2.75rem;height:2.75rem;border:1px solid #94a3b8;border-radius:.5rem;background:#fff;color:#1b2230;font-weight:700;cursor:pointer}",
    ".cbp-rate:hover span{background:var(--cbp-s);color:var(--cbp-sc)}",
    ".cbp-rate input:checked+span{background:var(--cbp-p);border-color:var(--cbp-p);color:var(--cbp-pc)}",
    ".cbp-ends{display:flex;justify-content:space-between;max-width:20rem;margin-top:.35rem;font-size:.8em;opacity:.8}",
    ".cbp-score>ul>li>strong{display:block;margin-bottom:.25rem;font-size:1.1em}",
    ".cbp-score>ul>li>span{display:block}",
    ".cbp-enhanced>ul>li{display:none}",
    ".cbp-enhanced>ul>li.cbp-show{display:block;margin-top:1rem;padding:1rem 1.25rem;background:#fff;border:2px solid var(--cbp-p);border-radius:.75rem}",
    ".cbp-total{margin:1rem 0 0;font-weight:700}",
    /* quiz */
    ".cbp-step{margin:.25rem 0 1rem;font-size:.9em;font-weight:600}",
    ".cbp-quiz>ol>li>strong{display:block;margin-bottom:.75rem;font-size:1.05em}",
    ".cbp-quiz>ol>li>ul>li{margin:0 0 .5rem}",
    ".cbp button.cbp-choice{display:block;width:100%;padding:.8rem 1rem;border:1px solid #94a3b8;border-radius:.5rem;background:#fff;color:#1b2230;font:inherit;text-align:left;cursor:pointer;transition:background-color .15s ease,color .15s ease}",
    ".cbp button.cbp-choice:hover{background:var(--cbp-s);border-color:var(--cbp-s);color:var(--cbp-sc)}",
    ".cbp-quiz [data-outcomes]>div{padding:1.25rem 1.5rem;background:#fff;border:2px solid var(--cbp-p);border-radius:.75rem}",
    ".cbp-quiz [data-outcomes]>div>:last-child{margin-bottom:0}",
    /* switch */
    ".cbp-switch{padding:1rem 1.25rem}",
    ".cbp-seg{display:inline-flex;flex-wrap:wrap;margin-bottom:1rem;border:1px solid #94a3b8;border-radius:.5rem;overflow:hidden;background:#fff}",
    ".cbp-seg button{padding:.6rem 1.1rem;border:0;border-right:1px solid #94a3b8;background:#fff;color:#1b2230;font:inherit;font-weight:600;cursor:pointer;transition:background-color .15s ease,color .15s ease}",
    ".cbp-seg button:last-child{border-right:0}",
    ".cbp-seg button:hover{background:var(--cbp-s);color:var(--cbp-sc)}",
    ".cbp-seg button[aria-pressed=true]{background:var(--cbp-p);color:var(--cbp-pc)}",
    ".cbp-select{display:none;width:100%;margin-bottom:1rem;padding:.7rem 2.5rem .7rem 1rem;border:1px solid #94a3b8;border-radius:.5rem;font:inherit;font-weight:600;color:#1b2230;background-color:#fff;background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%231b2230' stroke-width='2'/%3E%3C/svg%3E\");background-repeat:no-repeat;background-position:right 1rem center;-webkit-appearance:none;appearance:none}",
    "@media (max-width:640px){.cbp-seg{display:none}.cbp-select{display:block}.cbp-switch{padding:.85rem 1rem}.cbp-switch>[data-label]{line-height:1.6}}",
    ".cbp-switch>[data-label]>:last-child{margin-bottom:0}",
    ".cbp-switch ul{list-style:disc;padding-left:1.25rem;margin:0 0 .75rem}",
    ".cbp-switch li{margin:0 0 .5rem}",
    ".cbp-switch h4{margin:0 0 .75rem}",
    ".cbp-switch .cbp-nojs{display:none}",
    /* stats */
    ".cbp-stats.cbp{display:grid;grid-template-columns:repeat(2,1fr);gap:.75rem;padding:0;border:0;background:none}",
    "@media (min-width:768px){.cbp-stats.cbp{grid-template-columns:repeat(4,1fr)}}",
    ".cbp-stats>div{padding:.85rem 1rem;border:1px solid var(--cbp-bd);border-radius:.75rem;background:#fff;color:#1b2230}",
    ".cbp-stats>div:nth-child(4n+1){background:var(--cbp-t1)}",
    ".cbp-stats>div:nth-child(4n+2){background:var(--cbp-t2)}",
    ".cbp-stats>div:nth-child(4n+3){background:var(--cbp-t3)}",
    ".cbp-stats>div:nth-child(4n+4){background:var(--cbp-ok);border-color:#a9dcd5}",
    ".cbp-stats>div>span{display:block;font-size:.75em;font-weight:700;letter-spacing:.06em;text-transform:uppercase;opacity:.7}",
    ".cbp-stats>div>strong{display:block;margin-top:.15rem;font-size:1.15em;line-height:1.3}",
    /* print one block */
    "@media print{body.cbp-printing *{visibility:hidden!important}body.cbp-printing .cbp-print-target,body.cbp-printing .cbp-print-target *{visibility:visible!important}body.cbp-printing .cbp-print-target{position:absolute;left:0;top:0;width:100%;border:0}.cbp-actions,.cbp-saved{display:none!important}}",
    "@media (prefers-reduced-motion:reduce){.cbp *{transition:none!important}}"
  ].join("\n");

  var uid = 0;
  var reduce = false;
  try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  var store = {
    get: function (k) { try { var r = window.localStorage.getItem(k); return r ? JSON.parse(r) : null; } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    del: function (k) { try { window.localStorage.removeItem(k); } catch (e) {} }
  };

  function h(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text != null) { e.textContent = text; }
    return e;
  }
  function nid(p) { uid += 1; return "cbp-" + p + "-" + uid; }
  function btn(text, cls, fn) {
    var b = h("button", "cbp-b" + (cls ? " " + cls : ""), text);
    b.type = "button";
    if (fn) { b.addEventListener("click", fn); }
    return b;
  }
  function kids(root, tag) {
    return [].filter.call(root.children, function (c) { return c.tagName === tag; });
  }
  function firstKid(root, tag) { return kids(root, tag)[0] || null; }
  function titleOf(root, fallback) {
    var t = root.querySelector("h3, h2, h4");
    return t ? t.textContent.trim() : fallback;
  }
  function key(root, type, i) {
    return "cbp:" + window.location.pathname + ":" + (root.getAttribute("data-id") || type + "-" + i);
  }
  function scrollTo(el) {
    if (!el) { return; }
    try { el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" }); }
    catch (e) { el.scrollIntoView(); }
  }
  function progress(label) {
    var wrap = h("div", "cbp-progress");
    var count = h("span", "cbp-count");
    count.setAttribute("aria-live", "polite");
    var track = h("div", "cbp-track");
    track.setAttribute("role", "progressbar");
    track.setAttribute("aria-label", label);
    track.setAttribute("aria-valuemin", "0");
    var fill = h("div", "cbp-fill");
    track.appendChild(fill);
    wrap.appendChild(count);
    wrap.appendChild(track);
    return {
      el: wrap,
      set: function (n, total) {
        count.textContent = n >= total && total ? "All " + total + " done" : n + " of " + total + " done";
        fill.style.width = (total ? Math.round((n / total) * 100) : 0) + "%";
        track.setAttribute("aria-valuemax", String(total));
        track.setAttribute("aria-valuenow", String(n));
      }
    };
  }
  function copyText(text, button) {
    var old = button.getAttribute("data-label") || button.textContent;
    button.setAttribute("data-label", old);
    function done(ok) {
      button.textContent = ok ? "Copied" : "Press Ctrl+C";
      setTimeout(function () { button.textContent = old; }, 1800);
    }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) {}
      document.body.removeChild(ta);
      done(ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else { fallback(); }
  }
  function slug(s) {
    return (s || "my-answers").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "my-answers";
  }

  /* ---------- Stats bar ---------- */
  function initStats(root) {
    var scope = root.closest(".page-content") || root.closest("article") || document.body;
    var wpm = parseInt(root.getAttribute("data-wpm"), 10) || 225;
    var words = null;
    function count() {
      if (words !== null) { return words; }
      var c = scope.cloneNode(true);
      [].forEach.call(c.querySelectorAll("script,style,[data-cbp=stats]"), function (n) { n.parentNode.removeChild(n); });
      var t = (c.textContent || "").trim();
      words = t ? t.split(/\s+/).length : 0;
      return words;
    }
    [].forEach.call(root.children, function (box) {
      var kind = box.getAttribute("data-stat");
      var val = box.querySelector("strong");
      if (!val) { return; }
      if (kind === "time") { val.textContent = Math.max(1, Math.round(count() / wpm)) + " min"; }
      if (kind === "length") { val.textContent = count().toLocaleString("en-US") + " words"; }
    });
  }

  /* ---------- Saved checklist ---------- */
  function initChecklist(root, i) {
    var k = key(root, "checklist", i);
    var st = store.get(k) || { done: {} };
    if (!st.done) { st.done = {}; }
    var list = firstKid(root, "UL");
    if (!list) { return; }
    var bar = progress(titleOf(root, "Checklist"));
    root.insertBefore(bar.el, list);
    var rows = [];
    [].forEach.call(list.children, function (li, n) {
      var id = li.getAttribute("data-id") || "i" + n;
      var label = h("label", "cbp-item");
      var cb = document.createElement("input");
      cb.type = "checkbox";
      var txt = h("div", "cbp-item-text");
      while (li.firstChild) { txt.appendChild(li.firstChild); }
      label.appendChild(cb);
      label.appendChild(txt);
      li.appendChild(label);
      cb.checked = !!st.done[id];
      cb.addEventListener("change", function () {
        if (cb.checked) { st.done[id] = true; } else { delete st.done[id]; }
        store.set(k, st);
        render();
      });
      rows.push({ li: li, cb: cb });
    });
    var msg = h("p", "cbp-msg");
    var actions = h("div", "cbp-actions");
    actions.appendChild(btn(root.getAttribute("data-reset") || "Start over", "cbp-quiet", function () {
      if (!window.confirm("Clear all ticks and start again?")) { return; }
      st.done = {};
      store.set(k, st);
      rows.forEach(function (r) { r.cb.checked = false; });
      render();
    }));
    root.appendChild(msg);
    root.appendChild(actions);
    function render() {
      var n = 0;
      rows.forEach(function (r) {
        r.li.classList.toggle("cbp-is-done", r.cb.checked);
        if (r.cb.checked) { n += 1; }
      });
      bar.set(n, rows.length);
      msg.textContent = rows.length && n === rows.length ? (root.getAttribute("data-done") || "All done.") : "";
    }
    render();
  }

  /* ---------- Guide tracker ---------- */
  function fitTop(root) {
    var top = 0;
    try {
      var cands = document.querySelectorAll("header, nav");
      for (var j = 0; j < cands.length; j++) {
        if (root.contains(cands[j])) { continue; }
        var cs = window.getComputedStyle(cands[j]);
        if (cs.position === "fixed" || cs.position === "sticky") {
          var r = cands[j].getBoundingClientRect();
          if (r.top <= 1 && r.height < 200) { top = Math.max(top, Math.round(r.height)); }
        }
      }
    } catch (e) {}
    root.style.setProperty("--cbp-top", top + "px");
  }
  function initGuide(root, i) {
    var k = key(root, "guide", i);
    var st = store.get(k) || { done: {} };
    if (!st.done) { st.done = {}; }
    var list = firstKid(root, "OL");
    if (!list) { return; }
    var bar = progress(titleOf(root, "Guide steps"));
    root.insertBefore(bar.el, list);
    var steps = [];
    [].forEach.call(list.children, function (li, n) {
      var id = li.getAttribute("data-id") || "s" + n;
      var label = h("label", "cbp-donebox");
      var cb = document.createElement("input");
      cb.type = "checkbox";
      label.appendChild(cb);
      label.appendChild(document.createTextNode(" " + (root.getAttribute("data-donelabel") || "Done")));
      li.appendChild(label);
      cb.checked = !!st.done[id];
      cb.addEventListener("change", function () {
        if (cb.checked) { st.done[id] = true; } else { delete st.done[id]; }
        store.set(k, st);
        render();
        if (cb.checked) {
          var next = null;
          for (var j = n + 1; j < steps.length; j++) { if (!steps[j].cb.checked) { next = steps[j].li; break; } }
          scrollTo(next || root.querySelector(".cbp-msg"));
        }
      });
      steps.push({ li: li, cb: cb });
    });
    var msg = h("p", "cbp-msg");
    var actions = h("div", "cbp-actions");
    actions.appendChild(btn(root.getAttribute("data-reset") || "Start over", "cbp-quiet", function () {
      if (!window.confirm("Clear all ticks and start the guide again?")) { return; }
      st.done = {};
      store.set(k, st);
      steps.forEach(function (s) { s.cb.checked = false; });
      render();
      scrollTo(bar.el);
    }));
    root.appendChild(msg);
    root.appendChild(actions);
    function render() {
      var n = 0;
      var current = null;
      steps.forEach(function (s) {
        s.li.classList.toggle("cbp-is-done", s.cb.checked);
        s.li.classList.remove("cbp-current");
        if (s.cb.checked) { n += 1; } else if (!current) { current = s.li; }
      });
      if (current) { current.classList.add("cbp-current"); }
      bar.set(n, steps.length);
      msg.textContent = steps.length && n === steps.length ? (root.getAttribute("data-done") || "Every step is done.") : "";
    }
    fitTop(root);
    window.addEventListener("resize", function () { fitTop(root); });
    render();
  }

  /* ---------- Reflect and write ---------- */
  function initReflect(root, i) {
    var k = key(root, "reflect", i);
    var st = store.get(k) || { a: {} };
    if (!st.a) { st.a = {}; }
    var list = firstKid(root, "OL");
    if (!list) { return; }
    var title = titleOf(root, "My answers");
    var rows = [];
    var timer = null;
    var saved = h("p", "cbp-saved");
    function grow(ta) {
      ta.style.height = "auto";
      ta.style.height = Math.max(ta.scrollHeight + 4, 96) + "px";
    }
    [].forEach.call(list.children, function (li, n) {
      var id = li.getAttribute("data-id") || "q" + n;
      var q = li.querySelector("strong");
      var qtext = (q ? q.textContent : li.textContent).trim();
      if (q && !q.id) { q.id = nid("q"); }
      var ta = document.createElement("textarea");
      ta.rows = 4;
      if (q) { ta.setAttribute("aria-labelledby", q.id); } else { ta.setAttribute("aria-label", qtext); }
      ta.value = st.a[id] || "";
      ta.addEventListener("input", function () {
        grow(ta);
        st.a[id] = ta.value;
        saved.textContent = "";
        clearTimeout(timer);
        timer = setTimeout(function () {
          store.set(k, st);
          saved.textContent = "Saved on this device";
        }, 500);
      });
      li.appendChild(ta);
      rows.push({ q: qtext, ta: ta });
      setTimeout(function () { grow(ta); }, 0);
    });
    function build() {
      var parts = [title];
      rows.forEach(function (r) { parts.push(r.q + "\n" + (r.ta.value.trim() || "(no answer yet)")); });
      return parts.join("\n\n") + "\n";
    }
    var actions = h("div", "cbp-actions");
    actions.appendChild(btn(root.getAttribute("data-copy") || "Copy my answers", "", function (e) { copyText(build(), e.currentTarget); }));
    actions.appendChild(btn("Download", "cbp-quiet", function () {
      try {
        var blob = new Blob([build()], { type: "text/plain;charset=utf-8" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = slug(title) + ".txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      } catch (e) {}
    }));
    actions.appendChild(btn("Print", "cbp-quiet", function () {
      rows.forEach(function (r) { grow(r.ta); });
      root.classList.add("cbp-print-target");
      document.body.classList.add("cbp-printing");
      var clean = function () {
        root.classList.remove("cbp-print-target");
        document.body.classList.remove("cbp-printing");
        window.removeEventListener("afterprint", clean);
      };
      window.addEventListener("afterprint", clean);
      window.print();
    }));
    actions.appendChild(btn("Clear", "cbp-quiet", function () {
      if (!window.confirm("Delete everything you wrote in this block?")) { return; }
      st.a = {};
      store.del(k);
      rows.forEach(function (r) { r.ta.value = ""; grow(r.ta); });
      saved.textContent = "";
    }));
    root.appendChild(actions);
    root.appendChild(saved);
  }

  /* ---------- Scorecard ---------- */
  function initScore(root, i) {
    var k = key(root, "score", i);
    var st = store.get(k) || { v: {} };
    if (!st.v) { st.v = {}; }
    var scale = Math.min(10, Math.max(2, parseInt(root.getAttribute("data-scale"), 10) || 5));
    var list = firstKid(root, "OL");
    var results = firstKid(root, "UL");
    if (!list) { return; }
    root.classList.add("cbp-enhanced");
    var rows = [];
    [].forEach.call(list.children, function (li, n) {
      var id = li.getAttribute("data-id") || "s" + n;
      var text = h("span", "cbp-statement");
      text.id = nid("s");
      while (li.firstChild) { text.appendChild(li.firstChild); }
      li.appendChild(text);
      var group = h("div", "cbp-rates");
      group.setAttribute("role", "radiogroup");
      group.setAttribute("aria-labelledby", text.id);
      var name = nid("g");
      for (var v = 1; v <= scale; v++) {
        var lab = h("label", "cbp-rate");
        var inp = document.createElement("input");
        inp.type = "radio";
        inp.name = name;
        inp.value = String(v);
        inp.checked = st.v[id] === v;
        (function (value, el) {
          el.addEventListener("change", function () {
            st.v[id] = value;
            store.set(k, st);
            render();
          });
        })(v, inp);
        lab.appendChild(inp);
        lab.appendChild(h("span", "", String(v)));
        group.appendChild(lab);
      }
      li.appendChild(group);
      var low = root.getAttribute("data-low");
      var high = root.getAttribute("data-high");
      if (low || high) {
        var ends = h("div", "cbp-ends");
        ends.appendChild(h("span", "", low || ""));
        ends.appendChild(h("span", "", high || ""));
        li.appendChild(ends);
      }
      rows.push({ id: id, inputs: group.querySelectorAll("input") });
    });
    var total = h("p", "cbp-total");
    total.setAttribute("aria-live", "polite");
    var actions = h("div", "cbp-actions");
    actions.appendChild(btn("Start again", "cbp-quiet", function () {
      st.v = {};
      store.set(k, st);
      rows.forEach(function (r) { [].forEach.call(r.inputs, function (x) { x.checked = false; }); });
      render();
    }));
    root.insertBefore(total, results);
    root.insertBefore(actions, results);
    function render() {
      var answered = 0;
      var sum = 0;
      rows.forEach(function (r) {
        if (st.v[r.id]) { answered += 1; sum += st.v[r.id]; }
      });
      var all = rows.length && answered === rows.length;
      total.textContent = all
        ? "Your score: " + sum + " out of " + (rows.length * scale)
        : answered + " of " + rows.length + " answered";
      if (results) {
        [].forEach.call(results.children, function (li) {
          var min = parseInt(li.getAttribute("data-min"), 10);
          var max = parseInt(li.getAttribute("data-max"), 10);
          li.classList.toggle("cbp-show", !!all && sum >= min && sum <= max);
        });
      }
    }
    render();
  }

  /* ---------- Pick your path quiz ---------- */
  function initQuiz(root, i) {
    var k = key(root, "quiz", i);
    var st = store.get(k) || { a: [] };
    if (!st.a) { st.a = []; }
    var list = firstKid(root, "OL");
    var box = root.querySelector("[data-outcomes]");
    if (!list || !box) { return; }
    var qs = [].slice.call(list.children);
    var outs = [].slice.call(box.children);
    var step = h("p", "cbp-step");
    step.setAttribute("aria-live", "polite");
    root.insertBefore(step, list);
    var retake = btn(root.getAttribute("data-retake") || "Take the quiz again", "cbp-quiet", function () {
      st.a = [];
      store.set(k, st);
      show();
    });
    var actions = h("div", "cbp-actions");
    actions.appendChild(retake);
    root.appendChild(actions);

    qs.forEach(function (q, n) {
      var answers = q.querySelector("ul");
      if (!answers) { return; }
      [].forEach.call(answers.children, function (li) {
        var to = li.getAttribute("data-to");
        var b = h("button", "cbp-choice", li.textContent.trim());
        b.type = "button";
        li.textContent = "";
        li.appendChild(b);
        b.addEventListener("click", function () {
          st.a[n] = to;
          st.a.length = n + 1;
          store.set(k, st);
          show();
        });
      });
    });

    function winner() {
      var tally = {};
      st.a.forEach(function (id) { tally[id] = (tally[id] || 0) + 1; });
      var best = null;
      var top = -1;
      outs.forEach(function (o) {
        var c = tally[o.getAttribute("data-id")] || 0;
        if (c > top) { top = c; best = o; }
      });
      return best;
    }
    function show() {
      var n = st.a.length;
      var finished = n >= qs.length;
      qs.forEach(function (q, idx) { q.style.display = !finished && idx === n ? "" : "none"; });
      var win = finished ? winner() : null;
      outs.forEach(function (o) { o.style.display = o === win ? "" : "none"; });
      box.style.display = finished ? "" : "none";
      actions.style.display = finished || n > 0 ? "" : "none";
      step.textContent = finished ? "Your result" : "Question " + (n + 1) + " of " + qs.length;
    }
    show();
  }

  /* ---------- Switch / tabs ---------- */
  var groups = {};
  function initSwitch(root, i) {
    var panels = [].filter.call(root.children, function (c) { return c.hasAttribute("data-label"); });
    if (!panels.length) { return; }
    var group = root.getAttribute("data-group");
    var k = group ? "cbp:group:" + group : key(root, "switch", i);
    var seg = h("div", "cbp-seg");
    seg.setAttribute("role", "group");
    seg.setAttribute("aria-label", root.getAttribute("data-title") || "Choose a version");
    var buttons = [];
    var select = h("select", "cbp-select");
    select.setAttribute("aria-label", root.getAttribute("data-title") || "Choose a version");
    function auto() {
      var want = root.getAttribute("data-default");
      if (root.getAttribute("data-auto") === "os") {
        var p = "";
        try { p = (navigator.userAgent || "") + " " + (navigator.platform || ""); } catch (e) {}
        want = /Win/i.test(p) ? "win" : /Mac|iPhone|iPad/i.test(p) ? "mac" : "linux";
      }
      if (!want) { return panels[0].getAttribute("data-label"); }
      var re = new RegExp(want, "i");
      for (var j = 0; j < panels.length; j++) {
        if (re.test(panels[j].getAttribute("data-label"))) { return panels[j].getAttribute("data-label"); }
      }
      return panels[0].getAttribute("data-label");
    }
    function apply(label) {
      panels.forEach(function (p, n) {
        var on = p.getAttribute("data-label") === label;
        p.style.display = on ? "" : "none";
        buttons[n].setAttribute("aria-pressed", on ? "true" : "false");
      });
      select.value = label;
    }
    function choose(label) {
      store.set(k, label);
      if (group) { (groups[group] || []).forEach(function (fn) { fn(label); }); } else { apply(label); }
    }
    panels.forEach(function (p) {
      p.id = p.id || nid("p");
      var b = h("button", "", p.getAttribute("data-label"));
      b.type = "button";
      b.setAttribute("aria-controls", p.id);
      b.addEventListener("click", function () { choose(p.getAttribute("data-label")); });
      seg.appendChild(b);
      buttons.push(b);
      var o = h("option", "", p.getAttribute("data-label"));
      o.value = p.getAttribute("data-label");
      select.appendChild(o);
    });
    select.addEventListener("change", function () { choose(select.value); });
    root.insertBefore(seg, panels[0]);
    root.insertBefore(select, panels[0]);
    var saved = store.get(k);
    var valid = panels.some(function (p) { return p.getAttribute("data-label") === saved; });
    function sync(label) {
      var ok = panels.some(function (p) { return p.getAttribute("data-label") === label; });
      if (ok) { apply(label); }
    }
    if (group) { (groups[group] = groups[group] || []).push(sync); }
    apply(valid ? saved : auto());
  }

  var builders = {
    stats: initStats,
    checklist: initChecklist,
    guide: initGuide,
    reflect: initReflect,
    score: initScore,
    quiz: initQuiz,
    "switch": initSwitch
  };

  function run(scope) {
    var roots = (scope || document).querySelectorAll("[data-cbp]:not([data-cbp-ready])");
    if (!roots.length) { return; }
    if (!document.getElementById("cbp-style")) {
      var s = document.createElement("style");
      s.id = "cbp-style";
      s.appendChild(document.createTextNode(CSS));
      document.head.appendChild(s);
    }
    var list = [].slice.call(roots).sort(function (a, b) {
      return (a.getAttribute("data-cbp") === "stats" ? 0 : 1) - (b.getAttribute("data-cbp") === "stats" ? 0 : 1);
    });
    list.forEach(function (root, i) {
      var type = root.getAttribute("data-cbp");
      var fn = builders[type];
      if (!fn) { return; }
      root.setAttribute("data-cbp-ready", "1");
      root.classList.add("cbp", "cbp-" + type);
      try { fn(root, i); } catch (e) { if (window.console) { console.warn("Content block failed:", type, e); } }
    });
  }

  window.cbpInit = run;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { run(); });
  } else { run(); }
})();
