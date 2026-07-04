const { fetch, Agent } = require('/root/openclaw/node_modules/undici');

const TOKEN = require('fs').readFileSync('/tmp/tg_token','utf8').trim();

const start = Date.now();
fetch('https://api.telegram.org/bot' + TOKEN + '/sendMessage', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    chat_id: 951887934,
    text: '🤖 Test da Node'
  }),
  signal: AbortSignal.timeout(10000)
})
.then(r => {
  console.log('Status:', r.status, 'time:', Date.now()-start, 'ms');
  return r.json();
})
.then(d => {
  if (d.ok) console.log('SUCCESS: message_id', d.result.message_id);
  else console.log('FAIL:', d.error_code, d.description);
})
.catch(e => console.log('NETWORK:', e));
