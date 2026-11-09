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

<p class="pub-intro">Research, websites and policy documents that use or mention GlobalArchive, The Fish Collective and CheckEM.</p>

{% assign all_items = site.data.publications | sort: "year" | reverse %}
{% assign sections = "paper|Peer-reviewed papers,website|Websites & media,policy|Policy & government documents" | split: "," %}

{% for section in sections %}
  {% assign parts = section | split: "|" %}
  {% assign items = all_items | where: "type", parts[0] %}
<h2 class="pub-section" id="{{ parts[0] }}">{{ parts[1] }} <span class="pub-count">{{ items | size }}</span></h2>
<div class="pub-list">
  {% for pub in items %}
    {% if pub.doi %}{% assign link = "https://doi.org/" | append: pub.doi %}{% else %}{% assign link = pub.url %}{% endif %}
    <div class="pub-card pub-{{ pub.type }}">
      <div class="pub-year">{{ pub.year }}</div>
      <div class="pub-text">
        <a href="{{ link }}" target="_blank" rel="noopener">
          <h3>{{ pub.title }}</h3>
        </a>
        <p class="pub-meta">
          {% if pub.authors %}{{ pub.authors }} &middot; {% endif %}
          {% if pub.journal %}<em>{{ pub.journal }}</em>{% elsif pub.source %}{{ pub.source }}{% endif %}
          {% if pub.mentions %}<span class="pub-tags">{% for m in pub.mentions %}<span class="pub-tag">{{ m }}</span>{% endfor %}</span>{% endif %}
        </p>
        <a class="pub-doi" href="{{ link }}" target="_blank" rel="noopener">{% if pub.doi %}doi.org/{{ pub.doi }}{% else %}{{ pub.url | remove: "https://" | remove: "http://" | truncate: 80 }}{% endif %}</a>
      </div>
    </div>
  {% else %}
    <p class="pub-empty">Nothing listed yet.</p>
  {% endfor %}
</div>
{% endfor %}
