import { getInsights } from './campaigns.js';

export async function analyzeCountries(accountId, opts = {}) {
  const insights = await getInsights(`act_${accountId}`, {
    level: 'account',
    breakdowns: 'country',
    datePreset: opts.datePreset || 'last_30d',
    timeRange: opts.timeRange,
    fields: 'country,spend,impressions,clicks,actions,cost_per_action_type',
  });

  const countries = insights.map((row) => {
    const spend = parseFloat(row.spend || 0);
    const purchases = row.actions?.find(a => a.action_type === 'purchase')?.value || 0;
    const leads = row.actions?.find(a => a.action_type === 'lead')?.value || 0;
    const cpaPurchase = row.cost_per_action_type?.find(a => a.action_type === 'purchase')?.value || null;
    const cpaLead = row.cost_per_action_type?.find(a => a.action_type === 'lead')?.value || null;

    return {
      country: row.country,
      spend,
      impressions: parseInt(row.impressions || 0),
      clicks: parseInt(row.clicks || 0),
      purchases: parseInt(purchases),
      leads: parseInt(leads),
      cpa_purchase: cpaPurchase ? parseFloat(cpaPurchase) : null,
      cpa_lead: cpaLead ? parseFloat(cpaLead) : null,
    };
  });

  // Ordenar por CPA de purchase (mejor a peor), los sin datos al final
  countries.sort((a, b) => {
    if (a.cpa_purchase === null && b.cpa_purchase === null) return b.spend - a.spend;
    if (a.cpa_purchase === null) return 1;
    if (b.cpa_purchase === null) return -1;
    return a.cpa_purchase - b.cpa_purchase;
  });

  return countries;
}

export function printCountriesTable(countries) {
  console.log('\n' + '='.repeat(100));
  console.log('ANÁLISIS POR PAÍS — Ordenado por CPA (mejor a peor)');
  console.log('='.repeat(100));

  console.log(
    'País'.padEnd(8),
    'Gasto'.padStart(12),
    'Impresiones'.padStart(14),
    'Clicks'.padStart(10),
    'Compras'.padStart(10),
    'Leads'.padStart(8),
    'CPA Compra'.padStart(14),
    'CPA Lead'.padStart(12),
  );
  console.log('-'.repeat(100));

  for (const c of countries) {
    console.log(
      c.country.padEnd(8),
      `$${c.spend.toFixed(2)}`.padStart(12),
      c.impressions.toLocaleString().padStart(14),
      c.clicks.toLocaleString().padStart(10),
      String(c.purchases).padStart(10),
      String(c.leads).padStart(8),
      (c.cpa_purchase ? `$${c.cpa_purchase.toFixed(2)}` : '—').padStart(14),
      (c.cpa_lead ? `$${c.cpa_lead.toFixed(2)}` : '—').padStart(12),
    );
  }

  const totalSpend = countries.reduce((s, c) => s + c.spend, 0);
  const totalPurchases = countries.reduce((s, c) => s + c.purchases, 0);
  const totalLeads = countries.reduce((s, c) => s + c.leads, 0);
  console.log('-'.repeat(100));
  console.log(
    'TOTAL'.padEnd(8),
    `$${totalSpend.toFixed(2)}`.padStart(12),
    ''.padStart(14),
    ''.padStart(10),
    String(totalPurchases).padStart(10),
    String(totalLeads).padStart(8),
    (totalPurchases > 0 ? `$${(totalSpend / totalPurchases).toFixed(2)}` : '—').padStart(14),
    (totalLeads > 0 ? `$${(totalSpend / totalLeads).toFixed(2)}` : '—').padStart(12),
  );
  console.log('');
}
