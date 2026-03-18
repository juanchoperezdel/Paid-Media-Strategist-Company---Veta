import { getInsights } from './campaigns.js';

export async function analyzeAds(accountId, opts = {}) {
  const insights = await getInsights(`act_${accountId}`, {
    level: 'ad',
    datePreset: opts.datePreset || 'last_30d',
    timeRange: opts.timeRange,
    fields: 'ad_name,adset_name,campaign_name,spend,impressions,clicks,cpc,ctr,actions,cost_per_action_type,purchase_roas',
  });

  const ads = insights.map((row) => {
    const spend = parseFloat(row.spend || 0);
    const purchases = parseInt(row.actions?.find(a => a.action_type === 'purchase')?.value || 0);
    const leads = parseInt(row.actions?.find(a => a.action_type === 'lead')?.value || 0);
    const cpaPurchase = row.cost_per_action_type?.find(a => a.action_type === 'purchase')?.value;
    const roas = row.purchase_roas?.[0]?.value;

    return {
      ad_name: row.ad_name,
      adset_name: row.adset_name,
      campaign_name: row.campaign_name,
      spend,
      impressions: parseInt(row.impressions || 0),
      clicks: parseInt(row.clicks || 0),
      cpc: parseFloat(row.cpc || 0),
      ctr: parseFloat(row.ctr || 0),
      purchases,
      leads,
      cpa_purchase: cpaPurchase ? parseFloat(cpaPurchase) : null,
      roas: roas ? parseFloat(roas) : null,
    };
  });

  return ads;
}

export function printTopAds(ads, { sortBy = 'purchases', limit = 20 } = {}) {
  const sorted = [...ads].filter(a => a.spend > 0);

  if (sortBy === 'purchases') {
    sorted.sort((a, b) => b.purchases - a.purchases || (a.cpa_purchase || Infinity) - (b.cpa_purchase || Infinity));
  } else if (sortBy === 'cpa') {
    sorted.sort((a, b) => {
      if (a.cpa_purchase === null && b.cpa_purchase === null) return b.spend - a.spend;
      if (a.cpa_purchase === null) return 1;
      if (b.cpa_purchase === null) return -1;
      return a.cpa_purchase - b.cpa_purchase;
    });
  } else if (sortBy === 'roas') {
    sorted.sort((a, b) => (b.roas || 0) - (a.roas || 0));
  }

  const top = sorted.slice(0, limit);

  console.log('\n' + '='.repeat(120));
  console.log(`TOP ${limit} ADS — Ordenado por ${sortBy.toUpperCase()}`);
  console.log('='.repeat(120));

  console.log(
    '#'.padStart(3),
    'Ad Name'.padEnd(35),
    'Gasto'.padStart(12),
    'Impr'.padStart(10),
    'Clicks'.padStart(8),
    'CTR%'.padStart(7),
    'CPC'.padStart(8),
    'Compras'.padStart(9),
    'CPA'.padStart(10),
    'ROAS'.padStart(7),
  );
  console.log('-'.repeat(120));

  top.forEach((ad, i) => {
    const name = ad.ad_name.length > 33 ? ad.ad_name.slice(0, 32) + '…' : ad.ad_name;
    console.log(
      String(i + 1).padStart(3),
      name.padEnd(35),
      `$${ad.spend.toFixed(2)}`.padStart(12),
      ad.impressions.toLocaleString().padStart(10),
      ad.clicks.toLocaleString().padStart(8),
      `${ad.ctr.toFixed(2)}%`.padStart(7),
      `$${ad.cpc.toFixed(2)}`.padStart(8),
      String(ad.purchases).padStart(9),
      (ad.cpa_purchase ? `$${ad.cpa_purchase.toFixed(2)}` : '—').padStart(10),
      (ad.roas ? `${ad.roas.toFixed(2)}x` : '—').padStart(7),
    );
  });

  console.log('');
}
