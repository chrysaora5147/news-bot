const { json, requireAdmin, supabaseFetch } = require("./_shared");

module.exports = async function handler(request, response) {
  if (!requireAdmin(request, response)) return;

  if (request.method !== "GET") {
    json(response, 405, { error: "method not allowed" });
    return;
  }

  const env = {
    ADMIN_TOKEN: Boolean(process.env.ADMIN_TOKEN),
    SUPABASE_URL: Boolean(process.env.SUPABASE_URL),
    SUPABASE_SERVICE_ROLE_KEY: Boolean(process.env.SUPABASE_SERVICE_ROLE_KEY),
    LINE_CHANNEL_ACCESS_TOKEN: Boolean(process.env.LINE_CHANNEL_ACCESS_TOKEN),
    LINE_TO_IDS: Boolean(process.env.LINE_TO_IDS),
    LINE_BROADCAST: String(process.env.LINE_BROADCAST || "").toLowerCase() === "true",
    LINE_REQUIRE_APPROVAL: String(process.env.LINE_REQUIRE_APPROVAL || "true").toLowerCase() !== "false",
  };

  let supabase = { ok: false };
  try {
    await supabaseFetch("/rest/v1/articles?select=id&limit=1");
    supabase = { ok: true };
  } catch (error) {
    supabase = { ok: false, error: error.message };
  }

  json(response, 200, { env, supabase });
};
