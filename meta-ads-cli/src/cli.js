#!/usr/bin/env node
import 'dotenv/config';
import {
  listAccounts,
  listCampaigns,
  listAdSets,
  listAds,
  getInsights,
  getAdDailyInsights,
  getAdsWithMetadata,
  pauseObject,
  activateObject,
  updateBudget,
} from './campaigns.js';
import { analyzeCountries, printCountriesTable } from './analyze-countries.js';
import { analyzeAds, printTopAds } from './analyze-ads.js';

const [command, ...args] = process.argv.slice(2);

const HELP = `
meta-ads CLI — Gestionar Meta Ads desde la terminal

Comandos:
  accounts                              Listar cuentas publicitarias
  campaigns <account_id> [status]       Listar campañas (status: ACTIVE|PAUSED)
  adsets <account_id> [campaign_id]     Listar ad sets
  ads <account_id> [adset_id]           Listar ads
  insights <object_id> [opciones]       Ver métricas
    --level=campaign|adset|ad
    --date-preset=last_7d|last_30d|last_90d|this_month|last_month
    --time-range=YYYY-MM-DD,YYYY-MM-DD
    --breakdowns=age,gender,country,publisher_platform
  pause <object_id>                     Pausar campaña/adset/ad
  activate <object_id>                  Activar campaña/adset/ad
  budget <object_id> <monto> [--lifetime]  Cambiar presupuesto diario (o lifetime)
  countries <account_id> [--date-preset=X]   Análisis por país
  top-ads <account_id> [opciones]       Top ads por performance
    --sort=purchases|cpa|roas
    --limit=20
    --date-preset=last_30d

Ejemplos:
  node src/cli.js accounts
  node src/cli.js campaigns 123456789 ACTIVE
  node src/cli.js insights act_123456789 --level=campaign --date-preset=last_7d
  node src/cli.js countries 123456789
  node src/cli.js top-ads 123456789 --sort=cpa --limit=10
  node src/cli.js pause 120330011223344
  node src/cli.js budget 120330011223344 50.00
`;

function parseFlags(args) {
  const flags = {};
  const positional = [];
  for (const arg of args) {
    if (arg.startsWith('--')) {
      const [key, value] = arg.slice(2).split('=');
      flags[key] = value || true;
    } else {
      positional.push(arg);
    }
  }
  return { flags, positional };
}

async function main() {
  if (!command || command === 'help' || command === '--help') {
    console.log(HELP);
    return;
  }

  try {
    switch (command) {
      case 'accounts': {
        const accounts = await listAccounts();
        console.log(`\nCuentas publicitarias (${accounts.length}):\n`);
        for (const acc of accounts) {
          const status = ['', 'ACTIVE', 'DISABLED', 'UNSETTLED', '', '', '', 'PENDING_RISK_REVIEW', 'PENDING_SETTLEMENT', 'IN_GRACE_PERIOD', 'PENDING_CLOSURE', 'CLOSED', 'ANY_ACTIVE', 'ANY_CLOSED'][acc.account_status] || acc.account_status;
          console.log(`  ${acc.id.replace('act_', '')}  ${acc.name}  [${status}]  ${acc.currency}  Gastado: $${(parseInt(acc.amount_spent || 0) / 100).toFixed(2)}`);
        }
        break;
      }

      case 'campaigns': {
        const { positional, flags } = parseFlags(args);
        const accountId = positional[0];
        if (!accountId) { console.error('Uso: campaigns <account_id> [ACTIVE|PAUSED]'); return; }
        const status = positional[1] || flags.status;
        const campaigns = await listCampaigns(accountId, status);
        console.log(`\nCampañas (${campaigns.length}):\n`);
        for (const c of campaigns) {
          const budget = c.daily_budget
            ? `$${(parseInt(c.daily_budget) / 100).toFixed(2)}/día`
            : c.lifetime_budget
              ? `$${(parseInt(c.lifetime_budget) / 100).toFixed(2)} lifetime`
              : 'sin budget directo';
          console.log(`  ${c.id}  [${c.status}]  ${c.name}  (${budget})`);
        }
        break;
      }

      case 'adsets': {
        const { positional } = parseFlags(args);
        const accountId = positional[0];
        if (!accountId) { console.error('Uso: adsets <account_id> [campaign_id]'); return; }
        const campaignId = positional[1];
        const adsets = await listAdSets(accountId, campaignId);
        console.log(`\nAd Sets (${adsets.length}):\n`);
        for (const s of adsets) {
          const budget = s.daily_budget
            ? `$${(parseInt(s.daily_budget) / 100).toFixed(2)}/día`
            : s.lifetime_budget
              ? `$${(parseInt(s.lifetime_budget) / 100).toFixed(2)} lifetime`
              : 'CBO';
          console.log(`  ${s.id}  [${s.status}]  ${s.name}  (${budget})  opt: ${s.optimization_goal || '—'}`);
        }
        break;
      }

      case 'ads': {
        const { positional } = parseFlags(args);
        const accountId = positional[0];
        if (!accountId) { console.error('Uso: ads <account_id> [adset_id]'); return; }
        const adSetId = positional[1];
        const ads = await listAds(accountId, adSetId);
        console.log(`\nAds (${ads.length}):\n`);
        for (const ad of ads) {
          console.log(`  ${ad.id}  [${ad.status}]  ${ad.name}`);
        }
        break;
      }

      case 'insights': {
        const { positional, flags } = parseFlags(args);
        const objectId = positional[0];
        if (!objectId) { console.error('Uso: insights <object_id> [--level=X] [--date-preset=X]'); return; }

        const opts = {};
        if (flags.level) opts.level = flags.level;
        if (flags['date-preset']) opts.datePreset = flags['date-preset'];
        if (flags['time-range']) {
          const [since, until] = flags['time-range'].split(',');
          opts.timeRange = { since, until };
        }
        if (flags.breakdowns) opts.breakdowns = flags.breakdowns;
        if (flags.fields) opts.fields = flags.fields;

        const insights = await getInsights(objectId, opts);
        console.log(`\nInsights (${insights.length} filas):\n`);
        for (const row of insights) {
          console.log(`  ${row.campaign_name || row.adset_name || row.ad_name || objectId}`);
          console.log(`    Spend: $${row.spend}  |  Impr: ${row.impressions}  |  Clicks: ${row.clicks}  |  CPC: $${row.cpc || '—'}  |  CTR: ${row.ctr || '—'}%`);
          if (row.actions) {
            const purchases = row.actions.find(a => a.action_type === 'purchase');
            const leads = row.actions.find(a => a.action_type === 'lead');
            if (purchases) console.log(`    Compras: ${purchases.value}`);
            if (leads) console.log(`    Leads: ${leads.value}`);
          }
          if (row.purchase_roas?.[0]) {
            console.log(`    ROAS: ${parseFloat(row.purchase_roas[0].value).toFixed(2)}x`);
          }
          if (row.cost_per_action_type) {
            const cpaPurchase = row.cost_per_action_type.find(a => a.action_type === 'purchase');
            const cpaLead = row.cost_per_action_type.find(a => a.action_type === 'lead');
            if (cpaPurchase) console.log(`    CPA Compra: $${parseFloat(cpaPurchase.value).toFixed(2)}`);
            if (cpaLead) console.log(`    CPA Lead: $${parseFloat(cpaLead.value).toFixed(2)}`);
          }
          console.log('');
        }
        break;
      }

      case 'pause': {
        const objectId = args[0];
        if (!objectId) { console.error('Uso: pause <object_id>'); return; }
        await pauseObject(objectId);
        console.log(`✓ Pausado: ${objectId}`);
        break;
      }

      case 'activate': {
        const objectId = args[0];
        if (!objectId) { console.error('Uso: activate <object_id>'); return; }
        await activateObject(objectId);
        console.log(`✓ Activado: ${objectId}`);
        break;
      }

      case 'budget': {
        const { positional, flags } = parseFlags(args);
        const objectId = positional[0];
        const amount = parseFloat(positional[1]);
        if (!objectId || isNaN(amount)) { console.error('Uso: budget <object_id> <monto> [--lifetime]'); return; }
        const opts = flags.lifetime
          ? { lifetimeBudget: amount }
          : { dailyBudget: amount };
        await updateBudget(objectId, opts);
        console.log(`✓ Budget actualizado: ${objectId} → $${amount.toFixed(2)} ${flags.lifetime ? '(lifetime)' : '(diario)'}`);
        break;
      }

      case 'countries': {
        const { positional, flags } = parseFlags(args);
        const accountId = positional[0];
        if (!accountId) { console.error('Uso: countries <account_id> [--date-preset=X]'); return; }
        const countries = await analyzeCountries(accountId, { datePreset: flags['date-preset'] });
        printCountriesTable(countries);
        break;
      }

      case 'top-ads': {
        const { positional, flags } = parseFlags(args);
        const accountId = positional[0];
        if (!accountId) { console.error('Uso: top-ads <account_id> [--sort=X] [--limit=N]'); return; }
        const ads = await analyzeAds(accountId, { datePreset: flags['date-preset'] });
        printTopAds(ads, {
          sortBy: flags.sort || 'purchases',
          limit: parseInt(flags.limit) || 20,
        });
        break;
      }

      case 'daily': {
        // insights diarios por ad — output JSON para lifecycle analysis
        const { positional: dPos, flags: dFlags } = parseFlags(args);
        const dailyObjId = dPos[0];
        if (!dailyObjId) { console.error('Uso: daily <campaign_id|account_id> [--date-preset=X]'); return; }
        const dailyOpts = {};
        if (dFlags['date-preset']) dailyOpts.datePreset = dFlags['date-preset'];
        if (dFlags['time-range']) {
          const [since, until] = dFlags['time-range'].split(',');
          dailyOpts.timeRange = { since, until };
        }
        const dailyData = await getAdDailyInsights(dailyObjId, dailyOpts);

        // Flatten para que sea fácil de parsear
        const flatDaily = dailyData.map(row => ({
          ad_id: row.ad_id,
          ad_name: row.ad_name,
          adset_name: row.adset_name,
          campaign_name: row.campaign_name,
          date_start: row.date_start,
          date_stop: row.date_stop,
          spend: parseFloat(row.spend || 0),
          impressions: parseInt(row.impressions || 0),
          clicks: parseInt(row.clicks || 0),
          cpc: parseFloat(row.cpc || 0),
          ctr: parseFloat(row.ctr || 0),
          frequency: parseFloat(row.frequency || 0),
          purchases: row.actions?.find(a => a.action_type === 'purchase')?.value || 0,
          cost_per_purchase: row.cost_per_action_type?.find(a => a.action_type === 'purchase')?.value || null,
          roas: row.purchase_roas?.[0]?.value || null,
        }));
        // Output JSON puro (sin texto extra)
        console.log(JSON.stringify(flatDaily));
        break;
      }

      case 'ads-meta': {
        // metadata de ads con fechas de creación/modificación — output JSON
        const { positional: mPos, flags: mFlags } = parseFlags(args);
        const metaAccId = mPos[0];
        if (!metaAccId) { console.error('Uso: ads-meta <account_id> [campaign_id]'); return; }
        const metaCampId = mPos[1];
        const adsMeta = await getAdsWithMetadata(metaAccId, metaCampId);

        const flatMeta = adsMeta.map(ad => ({
          ad_id: ad.id,
          ad_name: ad.name,
          ad_status: ad.status,
          ad_created: ad.created_time,
          ad_updated: ad.updated_time,
          adset_id: ad.adset?.id || ad.adset_id,
          adset_name: ad.adset?.name,
          adset_status: ad.adset?.status,
          adset_created: ad.adset?.created_time,
          adset_updated: ad.adset?.updated_time,
          creative_id: ad.creative?.id,
          creative_title: ad.creative?.title,
          creative_body: ad.creative?.body,
        }));
        console.log(JSON.stringify(flatMeta));
        break;
      }

      default:
        console.error(`Comando desconocido: ${command}`);
        console.log(HELP);
    }
  } catch (err) {
    console.error(`\nError: ${err.message}`);
    process.exit(1);
  }
}

main();
