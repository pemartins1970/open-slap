const esbuild = require('esbuild');
const fs = require('fs');

// Check if a given line is inside JSX element content according to esbuild
// by wrapping it in various ways
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Parse just the problematic section with a proper wrapper
// Let's get lines 3820-3947 (the agentConfigModal block)
const snippet = lines.slice(3819, 3947).join('\n');
console.log('Testing agentConfigModal block (3820-3947)...');

// Wrap so it's in a function with return
const wrapped = 'const X = () => {\n  return (\n' + snippet + '\n  );\n};\nexport default X;\n';
try {
  esbuild.transformSync(wrapped, { loader: 'jsx' });
  console.log('OK');
} catch(e) {
  for (const err of e.errors) {
    console.log('  Error L' + err.location.line + ': ' + err.text);
    console.log('  Text: ' + err.location.lineText);
  }
}

// Now let's narrow it down: include 3820-3947 but EXCLUDE line 3822
// to see if the {agentConfigModal} is the problem
let modLines = [...lines.slice(3819, 3821), ...lines.slice(3822, 3947)];
const snippet2 = modLines.join('\n');
const wrapped2 = 'const X = () => {\n  return (\n' + snippet2 + '\n  );\n};\nexport default X;\n';

console.log('\nExcluding line 3822 (agentConfigModal)...');
try {
  esbuild.transformSync(wrapped2, { loader: 'jsx' });
  console.log('OK');
} catch(e) {
  for (const err of e.errors) {
    console.log('  Error L' + err.location.line + ': ' + err.text);
  }
}

// Now exclude the IIFE at 3862
const modLines2 = [...lines.slice(3819, 3861), ...lines.slice(3863, 3947)];
const snippet3 = modLines2.join('\n');
const wrapped3 = 'const X = () => {\n  return (\n' + snippet3 + '\n  );\n};\nexport default X;\n';

console.log('\nExcluding IIFE at 3862...');
try {
  esbuild.transformSync(wrapped3, { loader: 'jsx' });
  console.log('OK');
} catch(e) {
  for (const err of e.errors) {
    console.log('  Error L' + err.location.line + ': ' + err.text);
  }
}
