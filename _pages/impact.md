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

<p class="pub-intro">Research papers that have come from The Fish Collective, synthesised data, tools and standards it shares.</p>

<div class="pub-list">
  {% assign pubs = site.data.publications | sort: "year" | reverse %}
  {% for pub in pubs %}
    <div class="pub-card">
      <div class="pub-year">{{ pub.year }}</div>
      <div class="pub-text">
        <a href="https://doi.org/{{ pub.doi }}" target="_blank" rel="noopener">
          <h3>{{ pub.title }}</h3>
        </a>
        <p class="pub-meta">{% if pub.authors %}{{ pub.authors }} &middot; {% endif %}<em>{{ pub.journal }}</em></p>
        <a class="pub-doi" href="https://doi.org/{{ pub.doi }}" target="_blank" rel="noopener">doi.org/{{ pub.doi }}</a>
      </div>
    </div>
  {% endfor %}
</div>
