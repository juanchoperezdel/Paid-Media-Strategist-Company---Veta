import { metaGet, metaPost, metaPaginate } from './api.js';

// ── Cuentas ──
export async function listAccounts() {
  const data = await metaGet('/me/adaccounts', {
    fields: 'id,name,account_status,currency,timezone_name,amount_spent',
    limit: '100',
  });
  return data.data;
}

// ── Campañas ──
export async function listCampaigns(accountId, statusFilter) {
  const params = {
    fields: 'id,name,status,objective,daily_budget,lifetime_budget,budget_remaining,start_time,stop_time',
  };
  if (statusFilter) {
    params.filtering = JSON.stringify([{ field: 'status', operator: 'IN', value: [statusFilter] }]);
  }
  return metaPaginate(`/act_${accountId}/campaigns`, params);
}

// ── Ad Sets ──
export async function listAdSets(accountId, campaignId) {
  const endpoint = campaignId
    ? `/${campaignId}/adsets`
    : `/act_${accountId}/adsets`;
  const params = {
    fields: 'id,name,status,daily_budget,lifetime_budget,targeting,optimization_goal,bid_strategy,start_time,end_time',
  };
  return metaPaginate(endpoint, params);
}

// ── Ads ──
export async function listAds(accountId, adSetId) {
  const endpoint = adSetId
    ? `/${adSetId}/ads`
    : `/act_${accountId}/ads`;
  const params = {
    fields: 'id,name,status,creative{id,name,title,body,image_url,thumbnail_url,video_id},adset_id',
  };
  return metaPaginate(endpoint, params);
}

// ── Insights ──
export async function getInsights(objectId, opts = {}) {
  const {
    level,
    datePreset,
    timeRange,
    breakdowns,
    fields = 'campaign_name,adset_name,ad_name,spend,impressions,clicks,cpc,cpm,ctr,actions,cost_per_action_type,conversions,purchase_roas',
  } = opts;

  const params = { fields };

  if (level) params.level = level;
  if (datePreset) params.date_preset = datePreset;
  if (timeRange) params.time_range = JSON.stringify(timeRange);
  if (breakdowns) params.breakdowns = breakdowns;

  return metaPaginate(`/${objectId}/insights`, params);
}

// ── Insights diarios por ad (para lifecycle analysis) ──
export async function getAdDailyInsights(objectId, opts = {}) {
  const {
    datePreset = 'last_90d',
    timeRange,
  } = opts;

  const params = {
    level: 'ad',
    fields: 'ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,cpc,ctr,frequency,actions,cost_per_action_type,purchase_roas',
    time_increment: '1',  // desglose diario
  };

  if (datePreset && !timeRange) params.date_preset = datePreset;
  if (timeRange) params.time_range = JSON.stringify(timeRange);

  return metaPaginate(`/${objectId}/insights`, params);
}

// ── Metadata de ads con fechas de creación/modificación ──
export async function getAdsWithMetadata(accountId, campaignId) {
  const endpoint = campaignId
    ? `/${campaignId}/ads`
    : `/act_${accountId}/ads`;
  const params = {
    fields: 'id,name,status,created_time,updated_time,creative{id,name,title,body,image_url,thumbnail_url},adset_id,adset{id,name,status,created_time,updated_time,optimization_goal,daily_budget,lifetime_budget}',
    limit: '500',
  };
  return metaPaginate(endpoint, params);
}

// ── Acciones: pausar / activar ──
export async function updateStatus(objectId, status) {
  return metaPost(`/${objectId}`, { status });
}

export async function pauseObject(objectId) {
  return updateStatus(objectId, 'PAUSED');
}

export async function activateObject(objectId) {
  return updateStatus(objectId, 'ACTIVE');
}

// ── Presupuesto ──
export async function updateBudget(objectId, { dailyBudget, lifetimeBudget }) {
  const body = {};
  if (dailyBudget) body.daily_budget = Math.round(dailyBudget * 100); // Meta usa centavos
  if (lifetimeBudget) body.lifetime_budget = Math.round(lifetimeBudget * 100);
  return metaPost(`/${objectId}`, body);
}
