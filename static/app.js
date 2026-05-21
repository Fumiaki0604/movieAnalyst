const videoId = new URLSearchParams(window.location.search).get('video_id');

let player = null;
let report = null;
let insightTimeline = [];
let currentIndex = -1;

const TYPE_COLOR = {
  fact:           'var(--fact)',
  interpretation: 'var(--interpretation)',
  issue:          'var(--issue)',
  advice:         'var(--advice)',
};
const TYPE_LABEL = {
  fact:           '事実',
  interpretation: '解釈',
  issue:          '問題点',
  advice:         'アドバイス',
};

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function fmtTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function resolveTimestamp(insight, timeline) {
  if (insight.timestamp_start != null) return insight.timestamp_start;
  const ids = insight.evidence_ids || [];
  if (!ids.length) return null;
  const ev = (timeline || []).find(e => e.event_id === ids[0]);
  return ev ? ev.start : null;
}

function esc(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ---------------------------------------------------------------------------
// Build sorted timeline from all insight types
// ---------------------------------------------------------------------------

function buildInsightTimeline(report) {
  const tl = report.evidence_timeline || [];
  const items = [];

  const sections = [
    ['facts',           'fact'],
    ['interpretations', 'interpretation'],
    ['issues',          'issue'],
    ['advice',          'advice'],
  ];

  for (const [key, type] of sections) {
    for (const item of (report[key] || [])) {
      const ts = resolveTimestamp(item, tl);
      if (ts !== null) {
        items.push({ type, timestamp: ts, data: item });
      }
    }
  }

  return items.sort((a, b) => a.timestamp - b.timestamp);
}

// ---------------------------------------------------------------------------
// Render helpers
// ---------------------------------------------------------------------------

function makeBadge(type) {
  return `<span class="badge badge-${type}">${TYPE_LABEL[type]}</span>`;
}

function makeInsightCard(item) {
  const { type, timestamp, data } = item;
  const header = `<div class="card-header">${makeBadge(type)}<span class="card-time">${fmtTime(timestamp)}</span></div>`;
  const title  = `<div class="card-title">${esc(data.label || data.title)}</div>`;

  let body = '';
  if (type === 'fact') {
    body = `<div class="card-body">${esc(data.description)}</div>`;

  } else if (type === 'interpretation') {
    body = `<div class="card-body">${esc(data.explanation)}</div>
            <div class="card-detail"><span class="detail-label">関連性</span>${esc(data.relevance)}</div>`;

  } else if (type === 'issue') {
    const sev = (data.severity || 'medium').toLowerCase();
    body = `<div class="card-body"><span class="severity severity-${sev}">${sev.toUpperCase()}</span> ${esc(data.description)}</div>`;

  } else if (type === 'advice') {
    const pri = (data.priority || 'medium').toLowerCase();
    body = `<div class="card-detail"><span class="detail-label">アクション</span>${esc(data.action)}</div>
            <div class="card-detail"><span class="detail-label">場面</span>${esc(data.context)}</div>
            <div class="card-detail"><span class="detail-label">確認</span>${esc(data.measure)}</div>
            <div class="card-detail"><span class="severity severity-${pri}">${pri.toUpperCase()}</span></div>`;
  }

  return `<div class="insight-card type-${type}">${header}${title}${body}</div>`;
}

// ---------------------------------------------------------------------------
// DOM updates
// ---------------------------------------------------------------------------

function renderInsightList() {
  const list = document.getElementById('insight-list');
  list.innerHTML = insightTimeline.map((item, i) => {
    const label = esc(item.data.label || item.data.title || '');
    return `<div class="list-item type-${item.type}" data-index="${i}" onclick="seekToInsight(${i})">
      <div class="list-dot" style="background:${TYPE_COLOR[item.type]}"></div>
      <div class="list-content">
        <div class="list-label">${TYPE_LABEL[item.type]}: ${label}</div>
        <div class="list-time">${fmtTime(item.timestamp)}</div>
      </div>
    </div>`;
  }).join('');
}

function renderMarkers() {
  if (!player || !player.getDuration) return;
  const duration = player.getDuration();
  if (!duration) { setTimeout(renderMarkers, 1000); return; }

  const bar = document.getElementById('marker-bar');
  bar.innerHTML = insightTimeline.map((item, i) => {
    const pct = (item.timestamp / duration) * 100;
    const label = esc(item.data.label || item.data.title || '');
    return `<div class="marker marker-${item.type}"
      style="left:${pct}%"
      title="${fmtTime(item.timestamp)} — ${label}"
      onclick="seekToInsight(${i})"></div>`;
  }).join('');
}

function updateNowPlaying(idx) {
  const el = document.getElementById('current-insight');
  if (idx < 0) {
    el.innerHTML = '<div class="placeholder">動画を再生するとインサイトが表示されます</div>';
  } else {
    el.innerHTML = makeInsightCard(insightTimeline[idx]);
  }
}

function updateComingNext(idx) {
  const el = document.getElementById('next-insight');
  const next = insightTimeline[idx + 1];
  if (!next) {
    el.innerHTML = '<div class="placeholder">-</div>';
    return;
  }
  const label = esc(next.data.label || next.data.title || '');
  el.innerHTML = `<div class="next-row" onclick="seekToInsight(${idx + 1})">
    <div class="list-dot" style="background:${TYPE_COLOR[next.type]}"></div>
    <span>${fmtTime(next.timestamp)} ${TYPE_LABEL[next.type]}: ${label}</span>
  </div>`;
}

function highlightListItem(idx) {
  document.querySelectorAll('.list-item').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });
  if (idx >= 0) {
    const active = document.querySelector(`.list-item[data-index="${idx}"]`);
    if (active) active.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

// ---------------------------------------------------------------------------
// Sync loop
// ---------------------------------------------------------------------------

function syncInsights() {
  if (!player || !player.getCurrentTime) return;
  const t = player.getCurrentTime();

  let idx = -1;
  for (let i = 0; i < insightTimeline.length; i++) {
    if (insightTimeline[i].timestamp <= t) idx = i;
    else break;
  }

  if (idx !== currentIndex) {
    currentIndex = idx;
    updateNowPlaying(idx);
    updateComingNext(idx);
    highlightListItem(idx);
  }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

function seekToInsight(idx) {
  if (player && player.seekTo) {
    player.seekTo(insightTimeline[idx].timestamp, true);
    player.playVideo();
  }
}

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

async function loadReport() {
  if (!videoId) {
    document.getElementById('summary-text').textContent = 'video_id が指定されていません';
    return;
  }

  const res = await fetch(`/api/report/${videoId}`);
  if (!res.ok) {
    document.getElementById('summary-text').textContent = 'レポートの読み込みに失敗しました';
    return;
  }

  report = await res.json();
  document.getElementById('summary-text').textContent = report.summary || '';
  insightTimeline = buildInsightTimeline(report);
  renderInsightList();
  updateNowPlaying(-1);
  updateComingNext(-1);
}

// ---------------------------------------------------------------------------
// YouTube IFrame API (global callback required)
// ---------------------------------------------------------------------------

function onYouTubeIframeAPIReady() {
  player = new YT.Player('player', {
    height: '100%',
    width: '100%',
    videoId: videoId,
    playerVars: { rel: 0, modestbranding: 1 },
    events: {
      onReady: () => {
        renderMarkers();
        setInterval(syncInsights, 200);
      },
    },
  });
}

document.addEventListener('DOMContentLoaded', loadReport);

// ---------------------------------------------------------------------------
// MD Export
// ---------------------------------------------------------------------------

function exportMd(e) {
  e.preventDefault();
  if (!videoId) return;
  const a = document.createElement('a');
  a.href = `/api/report/${videoId}/export.md`;
  a.download = `report_${videoId}.md`;
  a.click();
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

const chatHistory = [];  // [{role, content}]
let chatStreaming = false;

function appendChatMsg(role, text) {
  const msgs = document.getElementById('chat-messages');
  const placeholder = msgs.querySelector('.chat-placeholder');
  if (placeholder) placeholder.remove();

  const div = document.createElement('div');
  div.className = `chat-msg chat-msg-${role === 'user' ? 'user' : 'ai'}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

async function sendChat() {
  if (chatStreaming) return;
  const input = document.getElementById('chat-input');
  const btn = document.getElementById('chat-send-btn');
  const text = input.value.trim();
  if (!text || !videoId) return;

  input.value = '';
  chatHistory.push({ role: 'user', content: text });
  appendChatMsg('user', text);

  chatStreaming = true;
  btn.disabled = true;

  const aiDiv = appendChatMsg('assistant', '');
  let aiText = '';

  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id: videoId, messages: chatHistory }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      buf = parts.pop();
      for (const part of parts) {
        if (!part.startsWith('data: ')) continue;
        const msg = JSON.parse(part.slice(6));
        if (msg.text) {
          aiText += msg.text;
          aiDiv.textContent = aiText;
          document.getElementById('chat-messages').scrollTop = 9999;
        }
        if (msg.done || msg.error) break;
      }
    }
  } catch (err) {
    aiDiv.textContent = 'エラーが発生しました';
  }

  if (aiText) chatHistory.push({ role: 'assistant', content: aiText });
  chatStreaming = false;
  btn.disabled = false;
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault();
        sendChat();
      }
    });
  }
});
