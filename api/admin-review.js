const { json, readJson, requireAdmin, supabaseFetch } = require("./_shared");

module.exports = async function handler(request, response) {
  if (!requireAdmin(request, response)) return;

  if (request.method !== "PATCH") {
    json(response, 405, { error: "method not allowed" });
    return;
  }

  try {
    const body = await readJson(request);
    const id = String(body.id || "").trim();
    const action = String(body.action || "").trim();
    const note = String(body.note || "").trim().slice(0, 500);

    if (!id) {
      json(response, 400, { error: "missing id" });
      return;
    }

    let payload;
    if (action === "approve") {
      payload = {
        line_approved_at: new Date().toISOString(),
        line_rejected_at: null,
        line_review_note: note || null,
      };
    } else if (action === "reject") {
      payload = {
        line_candidate: false,
        line_approved_at: null,
        line_rejected_at: new Date().toISOString(),
        line_review_note: note || null,
      };
    } else if (action === "reset") {
      payload = {
        line_approved_at: null,
        line_rejected_at: null,
        line_review_note: null,
      };
    } else {
      json(response, 400, { error: "unknown action" });
      return;
    }

    const rows = await supabaseFetch(`/rest/v1/articles?id=eq.${encodeURIComponent(id)}&select=id,title_th,line_candidate,line_approved_at,line_rejected_at,line_sent_at`, {
      method: "PATCH",
      headers: { Prefer: "return=representation" },
      body: JSON.stringify(payload),
    });

    json(response, 200, { article: rows?.[0] || null });
  } catch (error) {
    json(response, 500, { error: error.message });
  }
};
