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

<h2 class="pub-section" id="core">Core Fish Collective papers</h2>
<p class="pub-intro">Papers published by the Fish Collective, describing its methods, tools and synthesis work.</p>
<div class="pub-list">
  {% for pub in core %}{% include impact-card.html pub=pub %}{% endfor %}
</div>

<h2 class="pub-section" id="reach">Reach</h2>
<p class="pub-intro">Work by others that cites our core papers, or uses or mentions GlobalArchive, The Fish Collective or CheckEM.</p>
<div class="impact-boxes">
  <div class="impact-box impact-box-main">
    <span class="impact-value" id="reach-total">&hellip;</span>
    <span class="impact-label">Papers reached in total</span>
  </div>
  <a class="impact-box" href="#citing">
    <span class="impact-value" id="citing-count">&hellip;</span>
    <span class="impact-label">Papers citing our core papers</span>
  </a>
  <a class="impact-box" href="#paper">
    <span class="impact-value">{{ papers | size }}</span>
    <span class="impact-label">Papers using or mentioning our tools</span>
  </a>
  <a class="impact-box" href="#policy">
    <span class="impact-value">{{ policy | size }}</span>
    <span class="impact-label">Policy &amp; government documents</span>
  </a>
</div>
<p class="impact-note">Citations from <a href="https://openalex.org" target="_blank" rel="noopener">OpenAlex</a>, updated live. Papers that both cite and mention our work are counted once in the total.</p>

<h2 class="pub-section" id="paper">Papers using or mentioning our tools <span class="pub-count">{{ papers | size }}</span></h2>
<div class="pub-list">
  {% for pub in papers %}{% include impact-card.html pub=pub %}{% endfor %}
</div>

{% if websites.size > 0 %}
<h2 class="pub-section" id="website">Websites &amp; media <span class="pub-count">{{ websites | size }}</span></h2>
<div class="pub-list">
  {% for pub in websites %}{% include impact-card.html pub=pub %}{% endfor %}
</div>
{% endif %}

<h2 class="pub-section" id="citing">Papers citing our core papers <span class="pub-count" id="citing-count-2">&hellip;</span></h2>
<details class="impact-details">
  <summary>Show all citing papers</summary>
  <div class="pub-list" id="citing-list"><p class="pub-empty">Loading from OpenAlex&hellip;</p></div>
</details>

<h2 class="pub-section" id="policy">Policy &amp; government documents <span class="pub-count">{{ policy | size }}</span></h2>
<div class="pub-list">
  {% for pub in policy %}{% include impact-card.html pub=pub %}{% else %}<p class="pub-empty">Nothing listed yet.</p>{% endfor %}
</div>

<script>
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
    var coreIds = [];
    parts.forEach(function (results) {
      results.forEach(function (w) {
        (byDoi[cleanDoi(w.doi)] || []).forEach(function (c) {
          var slot = c.querySelector(".pub-cites");
          if (slot) slot.textContent = "Cited by " + (w.cited_by_count || 0).toLocaleString();
          if (c.getAttribute("data-group") === "core") coreIds.push(w.id.split("/").pop());
        });
      });
    });
    return loadCiting(coreIds);
  }).catch(function () { fail(); });

  // 2. Every work citing any core paper (each counted once), newest first.
  function loadCiting(coreIds) {
    if (!coreIds.length) return fail();
    var coreSet = {};
    coreIds.forEach(function (id) { coreSet[id] = true; });
    var works = [];
    function page(cursor, n) {
      var url = API + "?filter=cites:" + coreIds.join("|") + "&sort=publication_date:desc&per_page=200&cursor=" +
        encodeURIComponent(cursor) + "&select=id,doi,title,publication_year,primary_location,authorships";
      return getJson(url).then(function (j) {
        works = works.concat(j.results || []);
        var next = j.meta && j.meta.next_cursor;
        return next && (j.results || []).length && n < 25 ? page(next, n + 1) : works;
      });
    }
    return page("*", 1).then(function (all) {
      // leave out the core papers citing each other
      all = all.filter(function (w) { return !coreSet[w.id.split("/").pop()]; });
      var union = mentionNoDoi + Object.keys(mentionDois).length;
      all.forEach(function (w) { if (!mentionDois[cleanDoi(w.doi)]) union++; });
      setText("citing-count", all.length.toLocaleString());
      setText("citing-count-2", all.length.toLocaleString());
      setText("reach-total", union.toLocaleString());
      render(all);
    });
  }

  function render(list) {
    var box = document.getElementById("citing-list");
    if (!box) return;
    box.innerHTML = "";
    list.forEach(function (w) {
      var link = w.doi || w.id;
      var auths = w.authorships || [];
      var first = auths.length ? ((auths[0].author || {}).display_name || "") : "";
      var who = auths.length > 1 ? first.split(" ").pop() + " et al." : first;
      var src = ((w.primary_location || {}).source || {}).display_name || "";
      var card = document.createElement("div");
      card.className = "pub-card pub-citing";
      card.innerHTML = '<div class="pub-year"></div><div class="pub-text"><a target="_blank" rel="noopener"><h3></h3></a>' +
        '<p class="pub-meta"></p><a class="pub-doi" target="_blank" rel="noopener"></a></div>';
      card.querySelector(".pub-year").textContent = w.publication_year || "";
      card.querySelector("h3").textContent = w.title || "Untitled";
      card.querySelector(".pub-meta").innerHTML = (who ? escapeHtml(who) + " &middot; " : "") + (src ? "<em>" + escapeHtml(src) + "</em>" : "");
      var links = card.querySelectorAll("a");
      links[0].href = link; links[1].href = link;
      links[1].textContent = link.replace(/^https?:\/\//, "");
      box.appendChild(card);
    });
    if (!list.length) box.innerHTML = '<p class="pub-empty">Nothing found yet.</p>';
  }

  function escapeHtml(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

  function fail() {
    ["citing-count", "citing-count-2", "reach-total"].forEach(function (id) { setText(id, "\u2013"); });
    var box = document.getElementById("citing-list");
    if (box) box.innerHTML = '<p class="pub-empty">Could not reach OpenAlex. Try reloading the page.</p>';
  }
})();
</script>
