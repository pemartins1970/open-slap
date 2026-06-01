import fs from 'fs';
const content = fs.readFileSync('./App_auth.jsx', 'utf8');
const lines = content.split('\n');

// 1. Remove broken function definition (lines 3775-3779)
// Pattern:   };\n  const renderMessageList = () => (\n                      {renderMessageList()}\n  );\n  return (
const brokenFn = [
  '  };',
  '  const renderMessageList = () => (',
  '                      {renderMessageList()}',
  '  );',
  '  return ('
];

// Verify the broken function exists
let foundBroken = false;
for (let i = 0; i <= lines.length - brokenFn.length; i++) {
  let match = true;
  for (let j = 0; j < brokenFn.length; j++) {
    if (lines[i + j] !== brokenFn[j]) { match = false; break; }
  }
  if (match) {
    foundBroken = true;
    console.log(`Found broken function at L${i+1}-L${i+brokenFn.length}, replacing...`);
    // Replace with just the first '  };' and '  return ('
    lines[i] = '  };';
    lines[i+1] = '  return (';
    for (let j = 2; j < brokenFn.length; j++) {
      lines[i + j] = null; // Remove extra lines
    }
    break;
  }
}

if (!foundBroken) {
  console.log('Broken function not found. Current state:');
  for (let i = 3773; i < Math.min(3783, lines.length); i++) {
    if (lines[i] !== null) console.log(`L${i+1}: ${JSON.stringify(lines[i].substring(0, 80))}`);
  }
} else {
  // Remove null lines
  const cleaned = lines.filter(l => l !== null);
  
  // 2. Find the inline messagesContainer block
  let startIdx = -1;
  let endIdx = -1;
  for (let i = 0; i < cleaned.length; i++) {
    if (cleaned[i] === '                      <div style={styles.messagesContainer}>') {
      startIdx = i;
      console.log(`Inline block starts at L${i+1}`);
    }
    // Find closing after start
    if (startIdx >= 0 && i > startIdx) {
      if (cleaned[i] === '                      </div>') {
        endIdx = i;
        console.log(`Inline block ends at L${i+1}`);
        break;
      }
    }
  }
  
  if (startIdx >= 0 && endIdx >= 0) {
    // Replace with function call
    cleaned[startIdx] = '                      {renderMessageList()}';
    for (let i = startIdx + 1; i <= endIdx; i++) {
      cleaned[i] = null;
    }
    console.log('Replaced inline block with function call');
    
    // 3. Insert function definition before '  return ('
    const fnBody = [];
    fnBody.push('  const renderMessageList = () => (');
    
    // Extract the messagesContainer content from the original inline block (before replacement)
    // We saved it in the cleaned array before replacement... but we already nulled it.
    // Instead, let's read from the current content
    // Actually, let's reconstruct from the original file backup
    
    fnBody.push('    <div style={styles.messagesContainer}>');
    
    // Read the DIV content from the current cleaned (before we nulled it)
    // Since we only nulled startIdx+1 to endIdx, the content is still accessible
    // But we already modified cleaned. Let me read from the original lines before modification.
    
    // Actually let me re-read the original file for the function body
    const origContent = fs.readFileSync('./App_auth.jsx', 'utf8');
    const origLines = origContent.split('\n');
    
    // Find the inline block in the original
    let origStart = -1;
    let origEnd = -1;
    for (let i = 0; i < origLines.length; i++) {
      if (origLines[i] === '                      <div style={styles.messagesContainer}>') {
        origStart = i;
        // Find matching closing
        for (let j = i + 1; j < origLines.length; j++) {
          if (origLines[j] === '                      </div>') {
            origEnd = j;
            break;
          }
        }
        break;
      }
    }
    
    if (origStart >= 0 && origEnd >= 0) {
      // Extract the inline block content and re-indent it
      // Opening: change 22 spaces to 4
      fnBody.push(origLines[origStart].replace(/^ {22}/, '    '));
      
      // Inner content: change 22-28 spaces to 6-8
      for (let i = origStart + 1; i < origEnd; i++) {
        const line = origLines[i];
        const trimmed = line.trimStart();
        const origIndent = line.length - trimmed.length;
        const newIndent = Math.max(6, origIndent - 22 + 4); // Reduce by 22, add 4, min 6
        fnBody.push(' '.repeat(newIndent) + trimmed);
      }
      
      // Closing: change 22 spaces to 4
      fnBody.push(origLines[origEnd].replace(/^ {22}/, '    '));
      fnBody.push('  );');
      
      // Insert before '  return ('
      for (let i = 0; i < cleaned.length; i++) {
        if (cleaned[i] === '  return (') {
          // Insert fnBody here
          cleaned.splice(i, 0, ...fnBody);
          break;
        }
      }
      
      console.log('Inserted function definition');
    } else {
      console.log('ERROR: Could not find inline block in original file');
    }
    
    // Write result
    const result = cleaned.filter(l => l !== null).join('\n');
    fs.writeFileSync('./App_auth.jsx', result, 'utf8');
    console.log('File written. Lines:', result.split('\n').length);
  } else {
    console.log('ERROR: Could not find inline block bounds');
    // Write current state anyway
    fs.writeFileSync('./App_auth.jsx', cleaned.join('\n'), 'utf8');
  }
}
