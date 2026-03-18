import 'dotenv/config';

const TOKEN = process.env.META_ACCESS_TOKEN;
const API_VERSION = process.env.META_API_VERSION || 'v21.0';
const BASE_URL = `https://graph.facebook.com/${API_VERSION}`;

if (!TOKEN) {
  console.error('ERROR: META_ACCESS_TOKEN no está definido en .env');
  process.exit(1);
}

export async function metaGet(endpoint, params = {}) {
  const url = new URL(`${BASE_URL}${endpoint}`);
  url.searchParams.set('access_token', TOKEN);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  const res = await fetch(url);
  const data = await res.json();

  if (data.error) {
    throw new Error(`Meta API Error: ${data.error.message} (code ${data.error.code})`);
  }
  return data;
}

export async function metaPost(endpoint, body = {}) {
  const url = new URL(`${BASE_URL}${endpoint}`);
  url.searchParams.set('access_token', TOKEN);

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();

  if (data.error) {
    throw new Error(`Meta API Error: ${data.error.message} (code ${data.error.code})`);
  }
  return data;
}

export async function metaPaginate(endpoint, params = {}, limit = 500) {
  let all = [];
  let url = new URL(`${BASE_URL}${endpoint}`);
  url.searchParams.set('access_token', TOKEN);
  url.searchParams.set('limit', String(limit));
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  while (url) {
    const res = await fetch(url);
    const data = await res.json();
    if (data.error) {
      throw new Error(`Meta API Error: ${data.error.message} (code ${data.error.code})`);
    }
    all = all.concat(data.data || []);
    url = data.paging?.next || null;
  }
  return all;
}
