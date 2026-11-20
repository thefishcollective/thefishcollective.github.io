---
permalink: /impact/
layout: splash
title: "Impact"
excerpt: ""
toc: false
classes: wide
header:
  overlay_color: "#5e616c"
  video:
    src: /assets/videos/EG-CPO-014_N.ferrugineus_and_busy_reef_7m_small.mp4
---

{% assign all_items = site.data.publications | sort: "year" | reverse %}
{% assign core = all_items | where_exp: "i", "i.core == true" %}
{% assign papers = all_items | where: "type", "paper" | where_exp: "i", "i.core != true" %}
{% assign websites = all_items | where: "type", "website" %}
{% assign policy = all_items | where: "type", "policy" %}
{% assign extra_citing = site.data.publications | where: "type", "citing" %}

<nav class="impact-toc" aria-label="On this page">
  <span class="impact-toc-label">On this page:</span>
  <a href="#core">Core outputs</a>
  <a href="#paper">Work using our tools</a>
  {% if websites.size > 0 %}<a href="#website">Websites &amp; media</a>{% endif %}
  <a href="#citing">Papers citing our core papers</a>
  <a href="#policy">Policy &amp; government documents</a>
</nav>

<p class="pub-intro">Papers and reports from the Fish Collective, and the work by others that cites them or mentions GlobalArchive, The Fish Collective, CheckEM or the Australian BRUVS Working Group.</p>
<div class="impact-boxes">
  <a class="impact-box impact-box-core" href="#core">
    <span class="impact-value">{{ core | size }}</span>
    <span class="impact-label">Core Fish Collective outputs</span>
    <span class="impact-sub" id="core-cites">&nbsp;</span>
  </a>
  <a class="impact-box impact-box-main" href="#paper">
    <span class="impact-value" id="reach-total"><span class="impact-loading" aria-label="Loading"><i></i><i></i><i></i></span></span>
    <span class="impact-label">Papers that cite or use our work</span>
  </a>
  <a class="impact-box" href="#policy">
    <span class="impact-value">{{ policy | size }}</span>
    <span class="impact-label">Policy &amp; government documents</span>
  </a>
</div>
<p class="impact-note">Each paper is counted once, even if it both cites and mentions our work. Citations from <a href="https://openalex.org" target="_blank" rel="noopener">OpenAlex</a>, updated live.</p>

<h2 class="pub-section" id="core">Core Fish Collective outputs</h2>
<p class="pub-intro">Papers published by the Fish Collective describing its methods, tools and synthesis work, and reports built on its synthesis data.</p>
<div class="pub-list">
  {% for pub in core %}{% include impact-card.html pub=pub %}{% endfor %}
</div>

<h2 class="pub-section" id="paper">Work using our tools <span class="pub-count">{{ papers | size }}</span></h2>
<div class="pub-list">
  {% for pub in papers %}{% include impact-card.html pub=pub %}{% endfor %}
</div>

{% if websites.size > 0 %}
<h2 class="pub-section" id="website">Websites &amp; media <span class="pub-count">{{ websites | size }}</span></h2>
<div class="pub-list">
  {% for pub in websites %}{% include impact-card.html pub=pub %}{% endfor %}
</div>
{% endif %}

<h2 class="pub-section" id="citing">Papers citing our core papers <span class="pub-count" id="citing-count-2"><span class="impact-loading" aria-label="Loading"><i></i><i></i><i></i></span></span></h2>
<details class="impact-details">
  <summary>Show all citing papers</summary>
  <div class="pub-list" id="citing-list"><p class="pub-empty"><span class="impact-loading" aria-label="Loading"><i></i><i></i><i></i></span> Loading from OpenAlex</p></div>
</details>

<h2 class="pub-section" id="policy">Policy &amp; government documents <span class="pub-count">{{ policy | size }}</span></h2>
<div class="pub-list">
  {% for pub in policy %}{% include impact-card.html pub=pub %}{% else %}<p class="pub-empty">Nothing listed yet.</p>{% endfor %}
</div>

<script>
// Papers citing core outputs that OpenAlex can't link (e.g. reports without a DOI), from _data/publications.yml
var EXTRA_CITING = {{ extra_citing | jsonify }};
(function () {
  var API = "https://api.openalex.org/works";
  var cleanDoi = function (d) { return (d || "").replace(/^https?:\/\/doi\.org\//i, "").toLowerCase(); };
  var setText = function (id, t) { var el = document.getElementById(id); if (el) el.textContent = t; };
  var getJson = function (url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  };

  // 1. Look up every card with a DOI: fills in "Cited by N" and gets the core papers' OpenAlex IDs.
  var cards = Array.prototype.slice.call(document.querySelectorAll(".pub-card[data-doi]"));
  var byDoi = {};
  cards.forEach(function (c) {
    var d = cleanDoi(c.getAttribute("data-doi"));
    (byDoi[d] = byDoi[d] || []).push(c);
  });
  var dois = Object.keys(byDoi), chunks = [];
  for (var i = 0; i < dois.length; i += 50) chunks.push(dois.slice(i, i + 50));
  var mentionDois = {}, mentionNoDoi = document.querySelectorAll('.pub-card.pub-paper:not(.pub-core):not([data-doi])').length;
  cards.forEach(function (c) { if (c.getAttribute("data-group") === "mention") mentionDois[cleanDoi(c.getAttribute("data-doi"))] = true; });

  Promise.all(chunks.map(function (list) {
    return getJson(API + "?per_page=50&select=id,doi,cited_by_count&filter=doi:" + list.map(encodeURIComponent).join("|"))
      .then(function (j) { return j.results || []; }).catch(function () { return []; });
  })).then(function (parts) {
    var coreIds = [], coreLabels = {}, coreCites = 0;
    parts.forEach(function (results) {
      results.forEach(function (w) {
        (byDoi[cleanDoi(w.doi)] || []).forEach(function (c) {
          var slot = c.querySelector(".pub-cites");
          if (slot) slot.textContent = "Cited by " + (w.cited_by_count || 0).toLocaleString();
          if (c.getAttribute("data-group") === "core") {
            coreIds.push(w.id.split("/").pop());
            coreLabels[w.id] = c.getAttribute("data-label") || "Core paper";
            coreCites += w.cited_by_count || 0;
          }
        });
      });
    });
    if (coreIds.length) setText("core-cites", "cited " + coreCites.toLocaleString() + " times in total");
    return loadCiting(coreIds, coreLabels);
  }).catch(function () { fail(); });

  // 2. Every work citing any core paper (each counted once), newest first.
  function loadCiting(coreIds, coreLabels) {
    if (!coreIds.length) return fail();
    var coreSet = {};
    coreIds.forEach(function (id) { coreSet[id] = true; });
    var works = [];
    // Numbered pages: OpenAlex only allows cursor paging with an API key.
    function page(n) {
      var url = API + "?filter=cites:" + coreIds.join("|") + "&sort=publication_date:desc&per_page=200&page=" + n +
        "&select=id,doi,title,publication_year,primary_location,authorships,referenced_works";
      return getJson(url).then(function (j) {
        var res = j.results || [];
        works = works.concat(res);
        var total = (j.meta && j.meta.count) || 0;
        return res.length && works.length < total && n < 25 ? page(n + 1) : works;
      });
    }
    return page(1).then(function (all) {
      // leave out the core papers citing each other
      all = all.filter(function (w) { return !coreSet[w.id.split("/").pop()]; });
      // add hand-entered citing papers; if OpenAlex already has one, just add its chips
      var seenDoi = {};
      all.forEach(function (w) { if (w.doi) seenDoi[cleanDoi(w.doi)] = w; });
      (window.EXTRA_CITING || []).forEach(function (e) {
        var d = cleanDoi(e.doi), hit = d && seenDoi[d];
        if (hit) { hit.extraCites = (hit.extraCites || []).concat(e.cites || []); return; }
        all.push({ id: e.doi ? "https://doi.org/" + e.doi : (e.url || e.title), doi: e.doi ? "https://doi.org/" + e.doi : null,
          url: e.url, title: e.title, publication_year: e.year, extraAuthors: e.authors,
          primary_location: { source: { display_name: e.journal || e.source || "" } }, extraCites: e.cites || [] });
      });
      all.sort(function (x, y) { return (y.publication_year || 0) - (x.publication_year || 0); });
      var union = mentionNoDoi + Object.keys(mentionDois).length;
      all.forEach(function (w) { if (!mentionDois[cleanDoi(w.doi)]) union++; });
      setText("citing-count-2", all.length.toLocaleString());
      setText("reach-total", union.toLocaleString());
      render(all, coreLabels);
    });
  }

  function render(list, coreLabels) {
    var box = document.getElementById("citing-list");
    if (!box) return;
    box.innerHTML = "";
    list.forEach(function (w) {
      var link = w.doi || w.url || w.id;
      var auths = w.authorships || [];
      var first = auths.length ? ((auths[0].author || {}).display_name || "") : "";
      var who = auths.length > 1 ? first.split(" ").pop() + " et al." : first;
      if (w.extraAuthors) who = w.extraAuthors;
      var src = ((w.primary_location || {}).source || {}).display_name || "";
      var card = document.createElement("div");
      card.className = "pub-card pub-citing";
      card.innerHTML = '<div class="pub-year"></div><div class="pub-text"><a target="_blank" rel="noopener"><h3></h3></a>' +
        '<p class="pub-meta"></p><a class="pub-doi" target="_blank" rel="noopener"></a></div>';
      card.querySelector(".pub-year").textContent = w.publication_year || "";
      card.querySelector("h3").textContent = w.title || "Untitled";
      // chips for the core paper(s) this work cites, oldest first
      var cited = (w.referenced_works || []).filter(function (r) { return coreLabels[r]; })
        .map(function (r) { return coreLabels[r]; })
        .concat(w.extraCites || [])
        .filter(function (l, i, arr) { return arr.indexOf(l) === i; })
        .sort(function (x, y) { return x.slice(-4) - y.slice(-4); });
      var chips = cited.length ? ' <span class="pub-tags">' + cited.map(function (l) {
        return '<span class="pub-tag pub-tag-cites">Cites ' + escapeHtml(l) + "</span>";
      }).join("") + "</span>" : "";
      card.querySelector(".pub-meta").innerHTML = (who ? escapeHtml(who) + " &middot; " : "") + (src ? "<em>" + escapeHtml(src) + "</em>" : "") + chips;
      var links = card.querySelectorAll("a");
      links[0].href = link; links[1].href = link;
      links[1].textContent = link.replace(/^https?:\/\//, "");
      box.appendChild(card);
    });
    if (!list.length) box.innerHTML = '<p class="pub-empty">Nothing found yet.</p>';
  }

  function escapeHtml(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

  function fail() {
    ["citing-count-2", "reach-total"].forEach(function (id) { setText(id, "\u2013"); });
    var box = document.getElementById("citing-list");
    if (box) box.innerHTML = '<p class="pub-empty">Could not reach OpenAlex. Try reloading the page.</p>';
  }
})();
</script>
