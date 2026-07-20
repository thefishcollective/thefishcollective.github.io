---
layout: splash
title: "Access data"
header:
  overlay_color: "#5e616c"
  video:
    src: /assets/videos/DM-BV-C4_Shipwreck_Rankins_25.4m_small.mp4
permalink: /data/
toc: true
---


<div class="features-row">
  {% for feature in site.datasets %}
    <div class="feature-card">
      <a href="{{ feature.external_url | default: feature.url }}" target="_blank" rel="noopener" class="feature-link">
        <div class="feature-image">
          <img src="{{ feature.image }}" alt="{{ feature.title }}">
        </div>
        <h3 class="feature-title">{{ feature.title }}</h3>
        {% if feature.excerpt %}
          <p class="feature-excerpt">{{ feature.excerpt }}</p>
        {% endif %}
        {% if feature.button %}
          <span class="feature-button">{{ feature.button }}</span>
        {% endif %}
      </a>
    </div>
  {% endfor %}
</div>
