function json(response, statusCode, payload) {
  response.statusCode = statusCode;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.end(JSON.stringify(payload));
}

function requireAdmin(request, response) {
  const expected = process.env.ADMIN_TOKEN;
  if (!expected) {
    json(response, 500, { error: "missing ADMIN_TOKEN on Vercel" });
    return false;
  }

  const header = request.headers["x-admin-token"] || "";
  if (header !== expected) {
    json(response, 401, { error: "invalid admin token" });
    return false;
  }

  return true;
}

function supabaseConfig() {
  const supabaseUrl = (process.env.SUPABASE_URL || "https://zaqvrwsooxdtkepaaunk.supabase.co").replace(/\/$/, "");
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceKey) {
    throw new Error("missing SUPABASE_SERVICE_ROLE_KEY");
  }
  return { supabaseUrl, serviceKey };
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  const body = Buffer.concat(chunks).toString("utf8").trim();
  return body ? JSON.parse(body) : {};
}

async function supabaseFetch(path, options = {}) {
  const { supabaseUrl, serviceKey } = supabaseConfig();
  const response = await fetch(`${supabaseUrl}${path}`, {
    ...options,
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(payload?.message || payload?.error || `Supabase request failed: ${response.status}`);
  }
  return payload;
}

module.exports = {
  json,
  requireAdmin,
  readJson,
  supabaseFetch,
};
