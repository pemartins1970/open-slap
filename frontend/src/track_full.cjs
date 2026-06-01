const fs = require('fs');
const lines = fs.readFileSync('./App_auth.jsx', 'utf8').split('\n');

let braceDepth = 0;
let parenDepth = 0;
let inString = null;

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  const bdBefore = braceDepth;
  const pdBefore = parenDepth;
  
  for (let j = 0; j < line.length; j++) {
    const ch = line[j];
    const prev = j > 0 ? line[j-1] : '';
    
    if (inString && prev === '\\') continue;
    
    if (!inString) {
      if (ch === "'" || ch === '"' || ch === '`') {
        inString = ch;
        continue;
      }
    } else if (ch === inString) {
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
  
  if ((braceDepth !== 0 || parenDepth !== 0) && i < 100) {
    console.log('L' + (i+1) + ' b=' + braceDepth + ' p=' + parenDepth + ' | ' + line.trim().substring(0, 70));
  }
}

// Print specific lines
for (const ln of [3475, 3822, 3862, 3922, 3923, 3924, 3932, 3933, 3937, 3945, 3947, 3960]) {
  const idx = ln - 1;
  // Need to recompute... let me just print current state
}

// Let me just search for where depth changes significantly
console.log("\nSearching for depth changes near 3900-3960...");
braceDepth = 0;
parenDepth = 0;
inString = null;

for (let i = 3460; i < 3970; i++) {
  const line = lines[i];
  
  for (let j = 0; j < line.length; j++) {
    const ch = line[j];
    const prev = j > 0 ? line[j-1] : '';
    
    if (inString && prev === '\\') continue;
    
    if (!inString) {
      if (ch === "'" || ch === '"' || ch === '`') {
        inString = ch;
        continue;
      }
    } else if (ch === inString) {
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
  
  if (i >= 3895 && i <= 3960) {
    console.log('L' + (i+1) + ' b=' + braceDepth + ' p=' + parenDepth + ' | ' + line.trim().substring(0, 70));
  }
}
