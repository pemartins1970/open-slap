const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Count braces/parens WITHOUT regex detection
// Use a simple approach: count all { } ( ) but track strings
let bDepth = 0, pDepth = 0;

for (let i = 0; i < lines.length; i++) {
  let line = lines[i];
  // Simple counting: remove string contents to avoid counting inside strings
  // Remove content between quotes (simple approach, not perfectly accurate for edge cases)
  let processed = '';
  let inString = false;
  let stringChar = '';
  let templateDepth = 0;
  
  for (let j = 0; j < line.length; j++) {
    let ch = line[j];
    let next = j + 1 < line.length ? line[j + 1] : null;
    
    if (inString) {
      if (ch === '\\' && next) { j++; continue; }
      if (ch === stringChar) { inString = false; }
      continue;
    }
    
    if (templateDepth > 0) {
      if (ch === '`' && templateDepth === 1) { templateDepth = 0; continue; }
      if (ch === '$' && next === '{') { templateDepth = 2; j++; continue; }
      if (ch === '}' && templateDepth === 2) { templateDepth = 1; j++; continue; }
      continue;
    }
    
    if (ch === '"' || ch === "'") { inString = true; stringChar = ch; continue; }
    if (ch === '`') { templateDepth = 1; templateDepth = 1; continue; }
    
    if (ch === '/' && next === '/') break; // line comment
    
    processed += ch;
  }
  
  for (let ch of processed) {
    if (ch === '{') bDepth++;
    if (ch === '}') bDepth--;
    if (ch === '(') pDepth++;
    if (ch === ')') pDepth--;
  }
  
  let lineNum = i + 1;
  if (lineNum >= 3820 && lineNum <= 3960) {
    console.log('L' + lineNum + ': b=' + bDepth + ' p=' + pDepth + ' | ' + line.trim().substring(0, 50));
  }
}

console.log('\nFINAL: b=' + bDepth + ' p=' + pDepth);
