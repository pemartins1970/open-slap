const esbuild = require('esbuild');
const fs = require('fs');
const lines = fs.readFileSync('./App_auth.jsx', 'utf8').split('\n');

// Track depth using a smarter approach - track JSX expression state
let braceDepth = 0;
let parenDepth = 0;
let inString = null; // null, "'", '"', or '`'
let inRegex = false;

for (let i = 0; i < Math.min(lines.length, 3970); i++) {
  const line = lines[i];
  let lastNonSpace = '';
  
  for (let j = 0; j < line.length; j++) {
    const ch = line[j];
    const prev = j > 0 ? line[j-1] : '';
    
    // Handle escapes inside strings
    if (inString && prev === '\\') continue;
    
    // Toggle string states
    if (!inString && !inRegex) {
      if (ch === "'" || ch === '"' || ch === '`') {
        inString = ch;
        continue;
      }
    } else if (inString && ch === inString) {
      inString = null;
      continue;
    }
    
    if (!inString) {
      if (ch === '{') braceDepth++;
      if (ch === '}') braceDepth--;
      if (ch === '(') parenDepth++;
      if (ch === ')') parenDepth--;
    }
  }
  
  if (i >= 3930 && i <= 3960) {
    console.log('L' + (i+1) + ' b=' + braceDepth + ' p=' + parenDepth + ' | ' + line.trim().substring(0, 60));
  }
}

console.log('FINAL: b=' + braceDepth + ' p=' + parenDepth);
