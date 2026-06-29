function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadAdminStories() {
  const config = window.NEWS_CONFIG || {};
  if (!config.supabaseUrl || !config.supabaseAnonKey) {
    throw new Error("ยังไม่ได้ตั้งค่า Supabase ใน config.js");
  }

  const endpoint = `${config.supabaseUrl.replace(/\/$/, "")}/rest/v1/articles?select=id,title_th,summary_th,category,source,source_count,source_urls,url,importance_score,trending_score,line_candidate,line_sent_at,published_at&importance_score=gte.50&order=trending_score.desc&order=importance_score.desc&limit=30`;
  const response = await fetch(endpoint, {
    headers: {
      apikey: config.supabaseAnonKey,
      Authorization: `Bearer ${config.supabaseAnonKey}`,
    },
  });

  if (!response.ok) {
    throw new Error(`โหลดข้อมูลไม่สำเร็จ: ${response.status}`);
  }

  return response.json();
}

function renderSummary(rows) {
  const candidates = rows.filter((row) => row.line_candidate && !row.line_sent_at).slice(0, 3);
  document.querySelector("#adminSummary").innerHTML = `
    <div>
      <strong>${rows.length}</strong>
      <span>ข่าวที่ตรวจได้</span>
    </div>
    <div>
      <strong>${candidates.length}/3</strong>
      <span>ข่าวที่พร้อมส่ง LINE</span>
    </div>
    <div>
      <strong>${rows.filter((row) => row.line_sent_at).length}</strong>
      <span>ข่าวที่เคยส่งแล้ว</span>
    </div>
  `;
}

function renderRows(rows) {
  const candidates = new Set(
    rows
      .filter((row) => row.line_candidate && !row.line_sent_at)
      .slice(0, 3)
      .map((row) => row.id)
  );

  document.querySelector("#adminList").innerHTML = rows
    .map((row) => {
      const isCandidate = candidates.has(row.id);
      const sources = Array.isArray(row.source_urls) ? row.source_urls : [];
      return `
        <article class="admin-row ${isCandidate ? "candidate" : ""}">
          <div class="admin-row-main">
            <div class="card-meta">
              <span>${escapeHtml(row.category)}</span>
              <span>${row.trending_score || row.importance_score || 0}/100</span>
              <span>${row.source_count || 1} แหล่งข่าว</span>
            </div>
            <h2>${escapeHtml(row.title_th)}</h2>
            <p>${escapeHtml(row.summary_th)}</p>
            <div class="story-meta">
              <a href="${escapeHtml(row.url)}" target="_blank" rel="noreferrer">อ่านข่าวหลัก</a>
              ${sources
                .slice(0, 4)
                .map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.source || "source")}</a>`)
                .join("")}
            </div>
          </div>
          <div class="admin-status">
            <span>${isCandidate ? "จะส่ง LINE" : row.line_sent_at ? "ส่งแล้ว" : "เก็บไว้ดู"}</span>
          </div>
        </article>
      `;
    })
    .join("");
}

loadAdminStories()
  .then((rows) => {
    renderSummary(rows);
    renderRows(rows);
  })
  .catch((error) => {
    document.querySelector("#adminSummary").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  });
