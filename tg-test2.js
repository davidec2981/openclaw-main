const { Agent, fetch } = require('/root/openclaw/node_modules/undici');
const fs = require('fs');
const TOKEN = fs.readFileSync('/tmp/tg_token','utf8').trim();

async function test() {
  // Tentativo 1: autoSelectFamily=true (default del plugin)
  const d1 = new Agent({ connections: 10, pipelining: 1, keepAliveTimeout: 30000, keepAliveMaxTimeout: 600000, connect: { autoSelectFamily: true, autoSelectFamilyAttemptTimeout: 300, rejectUnauthorized: false } });
  const s1 = Date.now();
  try {
    const r = await fetch('https://api.telegram.org/bot' + TOKEN + '/getMe', { dispatcher: d1, signal: AbortSignal.timeout(15000) });
    const d = await r.json();
    console.log('T1 (autoSelectFamily):', Date.now()-s1, 'ms -', d.ok ? 'OK' : 'FAIL');
  } catch(e) { console.log('T1 FAIL:', Date.now()-s1, 'ms -', e.code); }

  // Tentativo 2: family=4 (sticky IPv4)
  const d2 = new Agent({ connections: 10, pipelining: 1, keepAliveTimeout: 30000, keepAliveMaxTimeout: 600000, connect: { family: 4, autoSelectFamily: false, rejectUnauthorized: false } });
  const s2 = Date.now();
  try {
    const r = await fetch('https://api.telegram.org/bot' + TOKEN + '/getMe', { dispatcher: d2, signal: AbortSignal.timeout(15000) });
    const d = await r.json();
    console.log('T2 (IPv4):', Date.now()-s2, 'ms -', d.ok ? 'OK' : 'FAIL');
  } catch(e) { console.log('T2 FAIL:', Date.now()-s2, 'ms -', e.code); }

  // Tentativo 3: family=4 no signal
  const s3 = Date.now();
  try {
    const d = await (await fetch('https://api.telegram.org/bot' + TOKEN + '/getMe')).json();
    console.log('T3 (default dispatcher):', Date.now()-s3, 'ms -', d.ok ? 'OK' : 'FAIL');
  } catch(e) { console.log('T3 FAIL:', Date.now()-s3, 'ms -', e.code); }

  await d1.close();
  await d2.close();
}
test();
