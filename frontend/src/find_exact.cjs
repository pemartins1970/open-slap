const esbuild = require('esbuild');
const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Function to parse from a given line and find where it fails
function findFirstError(startLine) {
  // Start building from startLine, extending by 1 line each time
  for (let end = startLine + 1; end <= lines.length; end++) {
    const snippet = lines.slice(0, end).join('\n');
    try {
      esbuild.transformSync(snippet, { loader: 'jsx' });
    } catch(e) {
      return {
        safeEnd: end - 1,
        errorLine: end,
        lineText: lines[end - 1],
        error: e.errors[0]
      };
    }
  }
  return null;
}

// Find where parsing first fails when starting from top
const result = findFirstError(0);
console.log('First parse failure at line ' + result.errorLine);
console.log('Line content: ' + result.lineText.trim());
console.log('Error: ' + result.error.text);
console.log('Error location: line ' + result.error.location.line + ', col ' + result.error.location.column);

// Now let's look at the safe area before failure
console.log('\nContext before failure:');
for (let i = Math.max(0, result.safeEnd - 3); i < result.safeEnd; i++) {
  console.log('  ' + (i+1) + ': ' + lines[i].trim().substring(0, 100));
}
console.log('>>> ' + (result.errorLine) + ': ' + lines[result.errorLine - 1].trim().substring(0, 100) + ' <<< FAILS');

// Now let's test what happens if we skip the error line
const snippetWithout = lines.slice(0, result.safeEnd).concat(lines.slice(result.errorLine)).join('\n');
try {
  esbuild.transformSync(snippetWithout, { loader: 'jsx' });
  console.log('\nWithout line ' + result.errorLine + ', file parses OK');
} catch(e) {
  console.log('\nWithout line ' + result.errorLine + ', still fails at line ' + e.errors[0].location.line + ': ' + e.errors[0].text);
}
