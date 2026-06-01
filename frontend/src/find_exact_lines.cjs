const esbuild = require('esbuild');
const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Test sections to narrow down
const tests = [
  { name: 'Top-3820', start: 0, end: 3820 },
  { name: 'Top-3822', start: 0, end: 3822 },
  { name: 'Top-3825', start: 0, end: 3825 },
  { name: 'Top-3900', start: 0, end: 3900 },
  { name: 'Top-3932', start: 0, end: 3932 },
  { name: 'Top-3933', start: 0, end: 3933 },
  { name: 'Top-3945', start: 0, end: 3945 },
  { name: 'Top-3946', start: 0, end: 3946 },
  { name: 'Top-3947', start: 0, end: 3947 },
];

for (const t of tests) {
  const snippet = lines.slice(t.start, t.end).join('\n') + '\nexport default {};\n';
  try {
    esbuild.transformSync(snippet, { loader: 'jsx' });
    console.log(t.name + ': OK');
  } catch(e) {
    console.log(t.name + ': FAIL at line ' + e.errors[0].location.line + ' - ' + e.errors[0].text.substring(0, 60));
  }
}

// Now test with the file up to 3945, and then add lines 3946, 3947, 3933 individually
console.log('\n--- Pinpoint test ---');

// Test up to 3945, add 3946
let s1 = lines.slice(0, 3945).join('\n') + '\n' + lines[3945] + '\nexport default {};\n';
try {
  esbuild.transformSync(s1, { loader: 'jsx' });
  console.log('+3946: OK');
} catch(e) {
  console.log('+3946: FAIL at ' + e.errors[0].location.line + ' - ' + e.errors[0].text.substring(0, 60));
}

// Test up to 3946, add 3947
let s2 = lines.slice(0, 3946).join('\n') + '\n' + lines[3946] + '\nexport default {};\n';
try {
  esbuild.transformSync(s2, { loader: 'jsx' });
  console.log('+3947: OK');
} catch(e) {
  console.log('+3947: FAIL at ' + e.errors[0].location.line + ' - ' + e.errors[0].text.substring(0, 60));
}

// Test replacing line 3946 with nothing
let s3 = lines.slice(0, 3945).concat(lines.slice(3946)).join('\n') + '\nexport default {};\n';
try {
  esbuild.transformSync(s3, { loader: 'jsx' });
  console.log('Without 3946: OK');
} catch(e) {
  console.log('Without 3946: FAIL at ' + e.errors[0].location.line + ' - ' + e.errors[0].text.substring(0, 60));
}
