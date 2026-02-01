#!/usr/bin/env node

/**
 * Show Canvas Dashboard
 *
 * This script generates the dashboard and outputs the render code.
 * Use the canvas tool's eval action to render it.
 *
 * Usage:
 *   node show-dashboard.js
 *   (Then use canvas tool with action=eval and the output)
 */

const fs = require('fs');
const path = require('path');

const renderCode = require('./render-dashboard.js');

// Output with instructions
console.log('// Copy the code below and use: canvas action=eval javaScript="<paste here>"');
console.log('//');
console.log('// Or use the interactive command:');
console.log('//   canvas action=eval javaScript="$(node show-dashboard.js)"');
console.log('//');
console.log(renderCode);
