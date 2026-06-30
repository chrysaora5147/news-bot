let currentRows = [];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function adminToken() {
  return localStorage.getItem("newsAdminToken") || "";
}

function setMessage(message, type = "") {
  const target = document.querySelector("#adminMessage");
  target.textContent = message;
  target.dataset.type = type;
}

async function loadAdminStories() {
  const config = window.NEWS_CONFIG || {};
  if (!config.supabaseUrl || !config.supabaseAnonKey) {
    throw new Error("ยังไม่ได้ตั้งค่า Supabase ใน config.js");
  }

  const endpoint = `${config.supabaseUrl.replace(/\/$/, "")}/rest/v1/articles?select=id,title_th,summary_th,category,source,source_count,source_urls,url,image_url,importance_score,trending_score,line_candidate,line_approved_at,line_rejected_at,line_review_note,line_sent_at,published_at&importance_score=gte.55&trending_score=gte.55&order=trending_score.desc&order=importance_score.desc&limit=40`;
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

function approvedRows(rows) {
  return rows
    .filter((row) => row.line_candidate && row.line_approved_at && !row.line_rejected_at && !row.line_sent_at)
    .sort((left, right) => (right.trending_score || right.importance_score || 0) - (left.trending_score || left.importance_score || 0))
    .slice(0, 3);
}

function suggestedRows(rows) {
  return rows
    .filter((row) => row.line_candidate && !row.line_rejected_at && !row.line_sent_at)
    .sort((left, right) => (right.trending_score || right.importance_score || 0) - (left.trending_score || left.importance_score || 0))
    .slice(0, 3);
}

function renderSummary(rows) {
  const approved = approvedRows(rows);
  const suggested = suggestedRows(rows);
  document.querySelector("#adminSummary").innerHTML = `
    <div>
      <strong>${rows.length}</strong>
      <span>ข่าวที่ตรวจได้</span>
    </div>
    <div>
      <strong>${approved.length}/3</strong>
      <span>ข่าวที่ approve แล้ว</span>
    </div>
    <div>
      <strong>${suggested.length}/3</strong>
      <span>ข่าวที่ระบบเสนอ</span>
    </div>
  `;
}

function statusText(row, isSuggested, isApproved) {
  if (row.line_sent_at) return "ส่งแล้ว";
  if (row.line_rejected_at) return "ไม่เอา";
  if (isApproved) return "พร้อมส่ง";
  if (isSuggested) return "ระบบเสนอ";
  return "เก็บไว้ดู";
}

function renderRows(rows) {
  const approved = new Set(approvedRows(rows).map((row) => row.id));
  const suggested = new Set(suggestedRows(rows).map((row) => row.id));

  document.querySelector("#adminList").innerHTML = rows
    .map((row) => {
      const isApproved = approved.has(row.id);
      const isSuggested = suggested.has(row.id);
      const sources = Array.isArray(row.source_urls) ? row.source_urls : [];
      const score = row.trending_score || row.importance_score || 0;
      return `
        <article class="admin-row ${isApproved ? "approved" : ""} ${isSuggested ? "candidate" : ""} ${row.line_rejected_at ? "rejected" : ""}">
          <div class="admin-row-main">
            <div class="card-meta">
              <span>${escapeHtml(row.category)}</span>
              <span>${score}/100</span>
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
          <div class="admin-actions">
            <span class="admin-badge">${statusText(row, isSuggested, isApproved)}</span>
            <button type="button" data-action="approve" data-id="${escapeHtml(row.id)}">Approve</button>
            <button type="button" data-action="reject" data-id="${escapeHtml(row.id)}">Reject</button>
            <button type="button" data-action="reset" data-id="${escapeHtml(row.id)}">Reset</button>
          </div>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => reviewArticle(button.dataset.id, button.dataset.action));
  });
}

async function refresh() {
  currentRows = await loadAdminStories();
  renderSummary(currentRows);
  renderRows(currentRows);
}

async function reviewArticle(id, action) {
  if (!adminToken()) {
    setMessage("ใส่ admin token ก่อน", "error");
    return;
  }

  setMessage("กำลังบันทึก...");
  const response = await fetch("/api/admin-review", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "x-admin-token": adminToken(),
    },
    body: JSON.stringify({ id, action }),
  });
  const payload = await response.json();
  if (!response.ok) {
    setMessage(payload.error || "บันทึกไม่สำเร็จ", "error");
    return;
  }

  setMessage("บันทึกแล้ว", "success");
  await refresh();
}

async function sendApprovedLine() {
  if (!adminToken()) {
    setMessage("ใส่ admin token ก่อน", "error");
    return;
  }

  setMessage("กำลังส่ง LINE...");
  const response = await fetch("/api/send-line", {
    method: "POST",
    headers: {
      "x-admin-token": adminToken(),
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    setMessage(payload.error || "ส่ง LINE ไม่สำเร็จ", "error");
    return;
  }

  setMessage(payload.sent ? `ส่งแล้ว ${payload.sent} ข่าว` : "ยังไม่มีข่าวที่ approve", "success");
  await refresh();
}

document.querySelector("#adminToken").value = adminToken();
document.querySelector("#saveTokenButton").addEventListener("click", () => {
  localStorage.setItem("newsAdminToken", document.querySelector("#adminToken").value.trim());
  setMessage("บันทึก token แล้ว", "success");
});
document.querySelector("#sendLineButton").addEventListener("click", sendApprovedLine);

refresh().catch((error) => {
  document.querySelector("#adminSummary").innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
});
