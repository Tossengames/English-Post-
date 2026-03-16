import { readFileSync, statSync } from 'fs';

const PAGE_ID = process.env.FB_PAGE_ID;
const PAGE_TOKEN = process.env.FB_PAGE_TOKEN;
const CAPTION = process.env.CAPTION;
const FILE = 'final.mp4';
const API = 'https://graph.facebook.com/v19.0';

if (!PAGE_ID || !PAGE_TOKEN) {
  console.error('Missing FB_PAGE_ID or FB_PAGE_TOKEN');
  process.exit(1);
}

const fileSize = statSync(FILE).size;
console.log('Uploading', (fileSize / 1024 / 1024).toFixed(2), 'MB');

const initRes = await fetch(`${API}/${PAGE_ID}/videos`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    upload_phase: 'start',
    file_size: fileSize,
    access_token: PAGE_TOKEN,
  }),
});
const init = await initRes.json();
if (!init.upload_session_id) {
  console.error('Session failed:', JSON.stringify(init));
  process.exit(1);
}

const { upload_session_id, video_id, start_offset, end_offset } = init;
const bytes = readFileSync(FILE);
const chunk = bytes.slice(Number(start_offset), Number(end_offset));

const form = new FormData();
form.append('upload_phase', 'transfer');
form.append('upload_session_id', upload_session_id);
form.append('start_offset', String(start_offset));
form.append('video_file_chunk', new Blob([chunk], { type: 'video/mp4' }), 'clip.mp4');
form.append('access_token', PAGE_TOKEN);

const xferRes = await fetch(`${API}/${PAGE_ID}/videos`, { method: 'POST', body: form });
const xfer = await xferRes.json();
if (xfer.error) {
  console.error('Transfer failed:', JSON.stringify(xfer));
  process.exit(1);
}

const finishRes = await fetch(`${API}/${PAGE_ID}/videos`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    upload_phase: 'finish',
    upload_session_id,
    description: CAPTION,
    published: true,
    access_token: PAGE_TOKEN,
  }),
});
const finish = await finishRes.json();

if (finish.success || finish.id) {
  console.log('Posted. Video ID:', video_id);
} else {
  console.error('Publish failed:', JSON.stringify(finish));
  process.exit(1);
}