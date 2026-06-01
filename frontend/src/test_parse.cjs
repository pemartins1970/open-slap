const esbuild = require('esbuild');
const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Test with the full App function: line 46 to 3960
const snippet1 = lines.slice(45, 3960).join('\n');
console.log('Testing lines 46-3960 (App function start)...');
try {
  const result = esbuild.transformSync(
    snippet1,
    { loader: 'jsx' }
  );
  console.log('OK');
} catch(e) {
  const err = e.errors[0];
  console.log('Error:', err?.text);
  console.log('Line:', err?.location?.line, 'Col:', err?.location?.column);
  // Print the error line and a few around it
  const errLine = err?.location?.line;
  const snippetLines = snippet1.split('\n');
  for (let i = Math.max(0, errLine-3); i < Math.min(snippetLines.length, errLine+2); i++) {
    console.log(`${i+1}: ${snippetLines[i]}`);
  }
}

// Also test even more of the file - start from the top
const snippet2 = lines.slice(0, 3960).join('\n');
console.log('\nTesting from top of file to 3960...');
try {
  const result = esbuild.transformSync(
    snippet2,
    { loader: 'jsx' }
  );
  console.log('OK');
} catch(e) {
  const err = e.errors[0];
  console.log('Error:', err?.text);
  console.log('Line:', err?.location?.line, 'Col:', err?.location?.column);
  console.log('Text:', err?.location?.lineText);
}
