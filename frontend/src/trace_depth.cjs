const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');

let lines = code.split('\n');
let braceDepth = 0;
let parenDepth = 0;
let bracketDepth = 0;
let inTemplate = false;
let templateDepth = 0;
let inString = false;
let stringChar = null;
let inRegex = false;

// Focus on the return statement from line 300 onward
for (let i = 299; i < lines.length; i++) {
  let line = lines[i];
  let inLine = false;
  let j = 0;
  
  // Simple char-by-char tracking (doesn't handle all edge cases but good enough)
  while (j < line.length) {
    let ch = line[j];
    let next = j + 1 < line.length ? line[j+1] : null;
    
    if (inString) {
      if (ch === '\\' && next) { j += 2; continue; }
      if (ch === stringChar) { inString = false; }
      j++; continue;
    }
    
    if (inRegex) {
      if (ch === '\\' && next) { j += 2; continue; }
      if (ch === '/') { inRegex = false; }
      j++; continue;
    }
    
    if (inTemplate) {
      if (ch === '`' && templateDepth === 0) { inTemplate = false; j++; continue; }
      if (ch === '$' && next === '{') { templateDepth++; j += 2; continue; }
      if (ch === '}' && templateDepth > 0) { templateDepth--; j++; continue; }
      if (ch === '\\' && next) { j += 2; continue; }
      j++; continue;
    }
    
    // Not in string/regex/template
    if (ch === '"' || ch === "'") { inString = true; stringChar = ch; j++; continue; }
    if (ch === '`') { inTemplate = true; j++; continue; }
    
    // Simple regex detection (after certain tokens)
    if (ch === '/' && next && next !== '*' && next !== '/') {
      // This could start a regex or division - rough heuristic
      let prev = j > 0 ? line[j-1] : null;
      if (prev === null || prev === '(' || prev === '=' || prev === '&' || prev === '|' || prev === '?' || prev === ':' || prev === ',' || prev === ';' || prev === '{' || prev === '!' || prev === '~' || prev === '^' || prev === '[') {
        inRegex = true; j++; continue;
      }
    }
    if (ch === '/' && next === '/') { break; } // line comment
    if (ch === '/' && next === '*') { j += 2; while (j < line.length - 1 && !(line[j] === '*' && line[j+1] === '/')) j++; j += 2; continue; }
    
    if (ch === '{') { braceDepth++; }
    else if (ch === '}') { braceDepth--; }
    else if (ch === '(') { parenDepth++; }
    else if (ch === ')') { parenDepth--; }
    else if (ch === '[') { bracketDepth++; }
    else if (ch === ']') { bracketDepth--; }
    
    j++;
  }
  
  // Check if this is around the problematic area
  if (i >= 3890 && i <= 3960) {
    let lineNum = i + 1;
    if (braceDepth !== 0 || parenDepth !== 0 || bracketDepth !== 0) {
      console.log(`LINE ${lineNum}: braces=${braceDepth} parens=${parenDepth} brackets=${bracketDepth} | ${line.trim().substring(0, 60)}`);
    }
  }
}

console.log(`\nFINAL: braces=${braceDepth} parens=${parenDepth} brackets=${bracketDepth}`);

// Now let me also check if there's a paren imbalance right before line 3947
// Let me check line 3945-3947
let checkLines = [3944, 3945, 3946, 3947, 3948];
console.log('\nDetailed context:');
for (let ln of checkLines) {
  let idx = ln - 1;
  if (idx >= 0 && idx < lines.length) {
    console.log(`${ln}: ${lines[idx]}`);
  }
}
