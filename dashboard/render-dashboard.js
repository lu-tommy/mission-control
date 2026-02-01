#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Load tasks data
const tasksPath = path.join(__dirname, 'tasks.json');
const tasks = JSON.parse(fs.readFileSync(tasksPath, 'utf-8'));

// Generate canvas rendering code
const renderCode = generateCanvasRender(tasks);

// Output the canvas-ready JavaScript code
console.log(renderCode);

function generateCanvasRender(tasks) {
  // Escape the tasks data for embedding
  const tasksEscaped = JSON.stringify(tasks);

  return `
// Canvas Dashboard Renderer
(function() {
  const canvas = document.querySelector('canvas');
  if (!canvas) {
    console.error('No canvas found');
    return;
  }

  const tasks = ${tasksEscaped};

  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;

  // Clear canvas
  ctx.fillStyle = '#1a1a2e';
  ctx.fillRect(0, 0, width, height);

  // Draw header
  drawHeader(ctx, width);

  // Draw active projects
  let y = 120;
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 20px system-ui, -apple-system, sans-serif';
  ctx.fillText('🟡 ACTIVE PROJECTS', 30, y);
  y += 40;

  tasks.active.forEach((proj, idx) => {
    y = drawProjectCard(ctx, proj, 30, y, width - 60, idx);
    y += 20;
  });

  // Draw completed
  y += 20;
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 20px system-ui, -apple-system, sans-serif';
  ctx.fillText('✅ RECENTLY DONE', 30, y);
  y += 40;

  tasks.completed.slice(0, 3).forEach((proj) => {
    y = drawCompletedItem(ctx, proj, 30, y, width - 60);
  });

  // Draw up next
  y += 20;
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 20px system-ui, -apple-system, sans-serif';
  ctx.fillText('⏳ UP NEXT', 30, y);
  y += 40;

  tasks.upNext.forEach((proj) => {
    y = drawUpNextItem(ctx, proj, 30, y, width - 60);
  });

  // Draw footer
  const dateStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  ctx.fillStyle = '#666666';
  ctx.font = '14px system-ui, -apple-system, sans-serif';
  ctx.fillText('Last updated: ' + dateStr, 30, height - 20);

  function drawHeader(ctx, width) {
    // Gradient header
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, '#667eea');
    gradient.addColorStop(1, '#764ba2');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, 80);

    // Title
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 32px system-ui, -apple-system, sans-serif';
    ctx.fillText('🦞 Productivity Dashboard', 30, 52);

    // Stats
    const activeCount = tasks.active.length;
    const completedCount = tasks.completed.length;
    ctx.font = '16px system-ui, -apple-system, sans-serif';
    ctx.fillText(\`\${activeCount} Active | \${completedCount} Completed\`, width - 200, 52);
  }

  function drawProjectCard(ctx, proj, x, y, cardWidth, idx) {
    const cardHeight = 140;
    const colors = {
      'in-progress': '#ffd93d',
      'blocked': '#ff6b6b',
      'review': '#6bcbff',
      'completed': '#6bcbff'
    };
    const priorityColors = {
      'high': '#ff6b6b',
      'medium': '#ffd93d',
      'low': '#6bcbff'
    };

    // Card background
    ctx.fillStyle = idx % 2 === 0 ? '#2d2d44' : '#252538';
    ctx.strokeStyle = '#3d3d5c';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(x, y, cardWidth, cardHeight, 12);
    ctx.fill();
    ctx.stroke();

    // Title
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 18px system-ui, -apple-system, sans-serif';
    ctx.fillText(proj.title, x + 15, y + 30);

    // Priority badge
    const priorityBadge = proj.priority.toUpperCase();
    ctx.fillStyle = priorityColors[proj.priority] || '#666';
    ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
    ctx.fillText(priorityBadge, x + cardWidth - 60, y + 25);

    // Progress bar
    const progressWidth = cardWidth - 30;
    const progressY = y + 45;

    // Background bar
    ctx.fillStyle = '#1a1a2e';
    ctx.beginPath();
    ctx.roundRect(x + 15, progressY, progressWidth, 24, 6);
    ctx.fill();

    // Progress fill
    ctx.fillStyle = colors[proj.status] || '#ffd93d';
    const fillWidth = (proj.progress / 100) * progressWidth;
    ctx.beginPath();
    ctx.roundRect(x + 15, progressY, fillWidth, 24, 6);
    ctx.fill();

    // Progress text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 14px system-ui, -apple-system, sans-serif';
    ctx.fillText(\`\${proj.progress}%\`, x + cardWidth - 35, progressY + 17);

    // Tasks
    ctx.fillStyle = '#aaaaaa';
    ctx.font = '14px system-ui, -apple-system, sans-serif';
    proj.tasks.slice(0, 3).forEach((task, taskIdx) => {
      const taskY = y + 85 + (taskIdx * 18);
      ctx.fillText(task, x + 20, taskY);
    });

    if (proj.tasks.length > 3) {
      ctx.fillStyle = '#666666';
      ctx.fillText(\`+\${proj.tasks.length - 3} more tasks\`, x + 20, y + 139);
    }

    return y + cardHeight;
  }

  function drawCompletedItem(ctx, proj, x, y, maxWidth) {
    ctx.fillStyle = '#888888';
    ctx.font = '14px system-ui, -apple-system, sans-serif';
    ctx.fillText('✓ ' + proj.title, x, y);

    ctx.fillStyle = '#666666';
    ctx.font = '12px system-ui, -apple-system, sans-serif';
    ctx.fillText(proj.completedAt, x + maxWidth - 80, y);

    return y + 20;
  }

  function drawUpNextItem(ctx, proj, x, y, maxWidth) {
    const priorityColors = {
      'high': '#ff6b6b',
      'medium': '#ffd93d',
      'low': '#6bcbff'
    };

    ctx.fillStyle = '#ffffff';
    ctx.font = '14px system-ui, -apple-system, sans-serif';
    ctx.fillText('→ ' + proj.title, x, y);

    ctx.fillStyle = priorityColors[proj.priority] || '#666666';
    ctx.font = '11px system-ui, -apple-system, sans-serif';
    ctx.fillText(proj.priority.toUpperCase(), x + maxWidth - 40, y);

    return y + 20;
  }

  console.log('Dashboard rendered successfully');
})();
  `;
}
