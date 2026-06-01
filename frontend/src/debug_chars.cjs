const fs = require('fs');
const lines = fs.readFileSync('./App_auth.jsx', 'utf8').split('\n');

for (let ln of [3946, 3947, 3945]) {
  const idx = ln - 1;
  const line = lines[idx];
  if (!line) { console.log('Line ' + ln + ': (undefined)'); continue; }
  console.log('Line ' + ln + ' (length=' + line.length + '):');
  for (let i = 0; i < line.length; i++) {
    const code = line.charCodeAt(i);
    console.log('  col ' + (i+1) + ': char=' + JSON.stringify(line[i]) + ' (hex=0x' + code.toString(16) + ')');
  }
}
