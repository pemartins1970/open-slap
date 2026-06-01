const esbuild = require('esbuild');
const fs = require('fs');
const code = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = code.split('\n');

// Test approach: replace `</div>` on line 3947 with `</div >` containing a space
// to see if it changes the error
let mod = [...lines];
mod[3946] = mod[3946].replace('</div>', '</div >');
try {
  esbuild.transformSync(mod.join('\n'), { loader: 'jsx' });
  console.log('Fix: OK');
} catch(e) {
  console.log('Fix: Error at L' + e.errors[0].location.line + ': ' + e.errors[0].text);
}

// Try: wrap line 3947 in a string expression
mod = [...lines];
mod[3946] = mod[3946].replace('</div>', '{/* end div */}');
try {
  esbuild.transformSync(mod.join('\n'), { loader: 'jsx' });
  console.log('Fix with comment: OK');
} catch(e) {
  console.log('Fix comment: Error at L' + e.errors[0].location.line + ': ' + e.errors[0].text);
}

// Try: add a semicolon before 3947 to end a JS statement
mod = [...lines];
mod.splice(3946, 0, '                 ;');
mod[3947] = mod[3947]; // keep 3947 as is
try {
  esbuild.transformSync(mod.join('\n'), { loader: 'jsx' });
  console.log('Fix with ; before 3947: OK');
} catch(e) {
  console.log('Fix with ;: Error at L' + e.errors[0].location.line + ': ' + e.errors[0].text);
}

// Try: replace `</div>` on 3946 with `</div >`
mod = [...lines];
mod[3945] = mod[3945].replace('</div>', '</div >');
try {
  esbuild.transformSync(mod.join('\n'), { loader: 'jsx' });
  console.log('Fix 3946: OK');
} catch(e) {
  console.log('Fix 3946: Error at L' + e.errors[0].location.line + ': ' + e.errors[0].text);
}

// Try: replace BOTH </div> with </div >
mod = [...lines];
mod[3945] = mod[3945].replace('</div>', '</div >');
mod[3946] = mod[3946].replace('</div>', '</div >');
try {
  esbuild.transformSync(mod.join('\n'), { loader: 'jsx' });
  console.log('Fix both: OK');
} catch(e) {
  console.log('Fix both: Error at L' + e.errors[0].location.line + ': ' + e.errors[0].text);
}

// Try: Comment out lines 3946-3947 and use non-JSX string
mod = [...lines];
mod[3945] = '{/* ' + mod[3945] + ' */}';
mod[3946] = '{/* ' + mod[3946] + ' */}';
try {
  esbuild.transformSync(mod.join('\n'), { loader: 'jsx' });
  console.log('Comment out: OK');
} catch(e) {
  console.log('Comment out: Error at L' + e.errors[0].location.line + ': ' + e.errors[0].text);
}
