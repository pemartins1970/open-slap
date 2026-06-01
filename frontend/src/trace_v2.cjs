const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

let b = 0, p = 0;

function countLine(line) {
  let inS = false, sc = null;
  let tDepth = 0; // 0=not in template, 1=in template body, 2=in ${} JS expr
  let j = 0;
  
  while (j < line.length) {
    let ch = line[j];
    let next = j + 1 < line.length ? line[j + 1] : null;
    
    if (inS) {
      if (ch === '\\' && next) { j += 2; continue; }
      if (ch === sc) inS = false;
      j++; continue;
    }
    
    if (tDepth > 0) {
      if (tDepth === 1 && ch === '`') { tDepth = 0; j++; continue; }
      if (tDepth === 1 && ch === '$' && next === '{') { tDepth = 2; j += 2; continue; }
      if (tDepth === 2) {
        if (ch === '{') { b++; j++; continue; }
        if (ch === '}') { b--; tDepth = 1; j++; continue; }
        if (ch === '(') { p++; j++; continue; }
        if (ch === ')') { p--; j++; continue; }
        if (ch === '"' || ch === "'") { inS = true; sc = ch; j++; continue; }
        if (ch === '\\' && next) { j += 2; continue; }
        if (ch === '/' && next === '/') break;
        if (ch === '/' && next === '*') { j += 2; while (j < line.length - 1 && !(line[j] === '*' && line[j+1] === '/')) j++; j += 2; continue; }
      }
      j++; continue;
    }
    
    if (ch === '"' || ch === "'") { inS = true; sc = ch; j++; continue; }
    if (ch === '`') { tDepth = 1; j++; continue; }
    if (ch === '/' && next === '/') break;
    if (ch === '/' && next === '*') { j += 2; while (j < line.length - 1 && !(line[j] === '*' && line[j+1] === '/')) j++; j += 2; continue; }
    
    if (ch === '{') b++;
    else if (ch === '}') b--;
    else if (ch === '(') p++;
    else if (ch === ')') p--;
    
    j++;
  }
}

// Check negative depths - find where depth goes below 0
let minB = 0, minP = 0;
for (let i = 0; i < lines.length; i++) {
  countLine(lines[i]);
  if (b < minB) {
    minB = b;
    console.log('Min brace depth ' + b + ' at line ' + (i+1));
  }
  if (p < minP) {
    minP = p;
    console.log('Min paren depth ' + p + ' at line ' + (i+1));
  }
}

console.log('FINAL: b=' + b + ' p=' + p);
console.log('Min: b=' + minB + ' p=' + minP);

// Now do another pass with the corrected counter
b = 0; p = 0;
console.log('\n=== Key lines with corrected depth ===');
for (let i = 0; i < lines.length; i++) {
  countLine(lines[i]);
  let ln = i + 1;
  if ([46, 300, 3476, 3667, 3820, 3822, 3890, 3897, 3900, 3902, 3907, 3922, 3933, 3937, 3945, 3946, 3947, 3960, 7787, 7887].includes(ln)) {
    console.log('L' + ln + ': b=' + b + ' p=' + p + ' | ' + lines[i].trim().substring(0, 60));
  }
}
