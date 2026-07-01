const { json, requireAdmin, supabaseFetch } = require("./_shared");

function envList(name) {
  return String(process.env[name] || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function lineBroadcastEnabled() {
  return String(process.env.LINE_BROADCAST || "").toLowerCase() === "true";
}

async function linePush(to, text) {
  const token = process.env.LINE_CHANNEL_ACCESS_TOKEN;
  if (!token) {
    throw new Error("missing LINE_CHANNEL_ACCESS_TOKEN");
  }

  const response = await fetch("https://api.line.me/v2/bot/message/push", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      to,
      messages: [{ type: "text", text: text.slice(0, 4900) }],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE push failed: ${response.status} ${body}`);
  }
}

async function lineBroadcast(text) {
  const token = process.env.LINE_CHANNEL_ACCESS_TOKEN;
  if (!token) {
    throw new Error("missing LINE_CHANNEL_ACCESS_TOKEN");
  }

  const response = await fetch("https://api.line.me/v2/bot/message/broadcast", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messages: [{ type: "text", text: text.slice(0, 4900) }],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE broadcast failed: ${response.status} ${body}`);
  }
}

function lineMessage(items) {
  const parts = ["ข่าวเด่นวันนี้"];
  for (const [index, item] of items.entries()) {
    const sourceCount = item.source_count || 1;
    parts.push(
      `${index + 1}. ${item.title_th || item.title}\n` +
        `สรุป: ${item.summary_th || item.summary}\n` +
        `ความดัง: ${item.trending_score || item.importance_score || 0}/100 | ${sourceCount} แหล่งข่าว\n` +
        `อ่านต่อ: ${item.url}`
    );
  }
  return parts.join("\n\n");
}

module.exports = async function handler(request, response) {
  if (!requireAdmin(request, response)) return;

  if (request.method !== "POST") {
    json(response, 405, { error: "method not allowed" });
    return;
  }

  try {
    const broadcast = lineBroadcastEnabled();
    const toIds = envList("LINE_TO_IDS");
    if (!broadcast && !toIds.length) {
      json(response, 500, { error: "missing LINE_TO_IDS" });
      return;
    }

    const select = [
      "id",
      "title",
      "title_th",
      "summary",
      "summary_th",
      "url",
      "source_count",
      "trending_score",
      "importance_score",
      "line_sent_at",
    ].join(",");
    const rows = await supabaseFetch(
      `/rest/v1/articles?select=${select}&line_candidate=eq.true&line_approved_at=not.is.null&line_rejected_at=is.null&line_sent_at=is.null&order=trending_score.desc&order=importance_score.desc&limit=3`
    );

    if (!rows.length) {
      json(response, 200, { sent: 0, message: "no approved LINE items" });
      return;
    }

    const text = lineMessage(rows);
    if (broadcast) {
      await lineBroadcast(text);
    } else {
      for (const to of toIds) {
        await linePush(to, text);
      }
    }

    const ids = rows.map((row) => row.id).join(",");
    await supabaseFetch(`/rest/v1/articles?id=in.(${ids})`, {
      method: "PATCH",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ line_sent_at: new Date().toISOString() }),
    });

    json(response, 200, { sent: rows.length, mode: broadcast ? "broadcast" : "push", titles: rows.map((row) => row.title_th || row.title) });
  } catch (error) {
    json(response, 500, { error: error.message });
  }
};
