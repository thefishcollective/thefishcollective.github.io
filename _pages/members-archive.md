---
title: Working Groups
layout: splash
permalink: /members/
collection: members
entries_layout: grid
classes: wide
header:
  overlay_color: "#5e616c"
  video:
    src: /assets/videos/GB-BV-P06_G.hebraicum_77cm_16.0m_small.mp4
---
## Australian Working Group
### Steering Committee
<div class="members-grid">
  {% for steering in site.steering %}
    <div class="member-card">
        <img src="{{ steering.image }}" alt="{{ steering.title }}">
        <h3>{{ steering.title }}</h3>
      <p class="steering-subtitle">{{ steering.excerpt }}</p>
    </div>
  {% endfor %}
</div>

### Working Group
<div class="members-grid">
  {% for member in site.members %}
    <div class="member-card">
        <img src="{{ member.image }}" alt="{{ member.title }}">
        <h3>{{ member.title }}</h3>
      <p class="member-subtitle">{{ member.excerpt }}</p>
    </div>
  {% endfor %}
</div>

## International Working Groups (In Development)
<div class="members-grid">
  {% for internationalgroup in site.internationalgroup %}
    <div class="member-card">
        <img src="{{ internationalgroup.image }}" alt="{{ internationalgroup.title }}">
        <h3>{{ internationalgroup.title }}</h3>
      <p class="member-subtitle">{{ internationalgroup.excerpt }}</p>
    </div>
  {% endfor %}
</div>

## Members
The following members have agreed to have their names and affiliations listed publicly.

{% raw %}
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">

<table id="members-table" class="display" style="width:100%">
  <thead>
    <tr>
      <th>Name</th>
      <th>Institute/Organisation/Affiliation</th>
    </tr>
  </thead>
  <tbody></tbody>
</table>

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>

<script>
document.addEventListener("DOMContentLoaded", function() {
  const sheetId = "1mH0FxPVJAqllZV5DAGlH585fGIHUgQA3WoZQ6LpQKDE"; // your sheet ID
  const gid = "837565785"; // your sheet tab GID
  const sheetUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:json&gid=${gid}`;

fetch(sheetUrl)
    .then(res => res.text())
    .then(text => {
      // Remove Google's JSONP wrapper
      const json = JSON.parse(text.substr(47).slice(0, -2));
      const rows = json.table.rows;
      const tableBody = document.querySelector("#members-table tbody");

      // Skip the first row (header)
      rows.slice(1).forEach(row => {
        const name = row.c[0] ? row.c[0].v : "";
        const affiliation = row.c[1] ? row.c[1].v : "";

        if (name && affiliation) {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${name}</td><td>${affiliation}</td>`;
          tableBody.appendChild(tr);
        }
      });

      // Initialize DataTables
      $('#members-table').DataTable({
      autoWidth: false
      });
    })
    .catch(err => console.error("Error loading data:", err));
});
</script>
{% endraw %}

