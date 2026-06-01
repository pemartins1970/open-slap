const esbuild = require('esbuild');
const fs = require('fs');

const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Test 1: remove arrow from line 3943
let mod = [...lines];
mod[3942] = mod[3942].replace('→', '-');
try { esbuild.transformSync(mod.join('\n'), { loader: 'jsx' }); console.log('Replace →: OK'); }
catch(e) { console.log('Replace →: L' + e.errors[0].location.line + ': ' + e.errors[0].text.substring(0,60)); }

// Test 2: simplify line 3943
mod = [...lines];
mod[3942] = '                      {t("sign_out")}';
try { esbuild.transformSync(mod.join('\n'), { loader: 'jsx' }); console.log('Simplify L3943: OK'); }
catch(e) { console.log('Simplify: L' + e.errors[0].location.line + ': ' + e.errors[0].text.substring(0,60)); }

// Test 3: remove isMobile ternary entirely, replace with just {null}
mod = [...lines];
mod[3936] = '                  {null}';  // replace the </button> line
mod.splice(3937, 8);  // remove lines 3938-3945
// Now lines are: ..., 3935, 3936({null}), 3937(original 3946 </div>), ...
try { esbuild.transformSync(mod.join('\n'), { loader: 'jsx' }); console.log('Remove ternary: OK'); }
catch(e) { console.log('Remove ternary: L' + e.errors[0].location.line + ': ' + e.errors[0].text.substring(0,60)
  + ' | ' + (e.errors[0].location.lineText||'').trim().substring(0,60)); }

// Test 4: remove lines 3937-3945 entirely (blank them out)
mod = [...lines];
for (let i = 3936; i <= 3944; i++) {
  mod[i] = '';
}
try { esbuild.transformSync(mod.join('\n'), { loader: 'jsx' }); console.log('Blank 3937-3945: OK'); }
catch(e) { console.log('Blank: L' + e.errors[0].location.line + ': ' + e.errors[0].text.substring(0,60)
  + ' | ' + (e.errors[0].location.lineText||'').trim().substring(0,60)); }

// Test 5: replace the )} on line 3945 with )}; (add semicolon)
mod = [...lines];
mod[3944] = mod[3944].replace(')}', ')};');
try { esbuild.transformSync(mod.join('\n'), { loader: 'jsx' }); console.log('Semicolon: OK'); }
catch(e) { console.log('Semicolon: L' + e.errors[0].location.line + ': ' + e.errors[0].text.substring(0,60)
  + ' | ' + (e.errors[0].location.lineText||'').trim().substring(0,60)); }
