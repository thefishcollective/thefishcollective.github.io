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
<p class="pub-intro">Work by others that uses or mentions GlobalArchive, The Fish Collective or CheckEM.</p>
<div class="impact-boxes">
  <a class="impact-box" href="#paper">
    <span class="impact-value">{{ papers | size }}</span>
    <span class="impact-label">Peer-reviewed papers</span>
  </a>
  <div class="impact-box">
    <span class="impact-value" id="mention-citations">&hellip;</span>
    <span class="impact-label">Citations of those papers</span>
  </div>
  <a class="impact-box" href="#policy">
    <span class="impact-value">{{ policy | size }}</span>
    <span class="impact-label">Policy &amp; government documents</span>
  </a>
  <div class="impact-box">
    <span class="impact-value" id="core-citations">&hellip;</span>
    <span class="impact-label">Citations of core papers</span>
  </div>
</div>
<p class="impact-note">Citation counts from <a href="https://openalex.org" target="_blank" rel="noopener">OpenAlex</a>, updated live.</p>

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

<h2 class="pub-section" id="policy">Policy &amp; government documents <span class="pub-count">{{ policy | size }}</span></h2>
<div class="pub-list">
  {% for pub in policy %}{% include impact-card.html pub=pub %}{% else %}<p class="pub-empty">Nothing listed yet.</p>{% endfor %}
</div>

<script>
(function () {
  // Look up live citation counts in OpenAlex for every card with a DOI.
  var cards = Array.prototype.slice.call(document.querySelectorAll(".pub-card[data-doi]"));
  if (!cards.length) return;
  var byDoi = {};
  cards.forEach(function (c) {
    var d = c.getAttribute("data-doi").toLowerCase();
    (byDoi[d] = byDoi[d] || []).push(c);
  });
  var dois = Object.keys(byDoi), chunks = [];
  for (var i = 0; i < dois.length; i += 50) chunks.push(dois.slice(i, i + 50));

  function fetchChunk(list) {
    var url = "https://api.openalex.org/works?per_page=50&select=doi,cited_by_count&filter=doi:" +
      list.map(encodeURIComponent).join("|");
    return fetch(url).then(function (r) { return r.ok ? r.json() : { results: [] }; })
      .then(function (j) { return j.results || []; })
      .catch(function () { return []; });
  }

  Promise.all(chunks.map(fetchChunk)).then(function (parts) {
    var totals = { core: 0, mention: 0 }, found = 0;
    parts.forEach(function (results) {
      results.forEach(function (w) {
        var d = (w.doi || "").replace(/^https?:\/\/doi\.org\//i, "").toLowerCase();
        (byDoi[d] || []).forEach(function (c) {
          found++;
          var n = w.cited_by_count || 0;
          totals[c.getAttribute("data-group")] += n;
          var slot = c.querySelector(".pub-cites");
          if (slot) slot.textContent = "Cited by " + n.toLocaleString();
        });
      });
    });
    var fmt = function (n) { return found ? n.toLocaleString() : "–"; };
    document.getElementById("core-citations").textContent = fmt(totals.core);
    document.getElementById("mention-citations").textContent = fmt(totals.mention);
  });
})();
</script>
