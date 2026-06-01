const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');

const esbuild = require('esbuild');
try {
  const result = esbuild.transformSync(code, { loader: 'jsx' });
  console.log('BUILD OK');
} catch(e) {
  console.log('Errors:');
  for (const err of e.errors) {
    console.log('  Line ' + err.location.line + ', Col ' + err.location.column + ': ' + err.text);
    console.log('  Text: ' + err.location.lineText);
  }
  if (e.warnings && e.warnings.length) {
    console.log('Warnings:');
    for (const w of e.warnings) {
      console.log('  Line ' + w.location.line + ', Col ' + w.location.column + ': ' + w.text);
      console.log('  Text: ' + w.location.lineText);
    }
  }
}
