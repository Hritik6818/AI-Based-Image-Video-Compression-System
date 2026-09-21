const f = document.getElementById('f'), o = document.getElementById('out'), c = document.getElementById('cmp');
const kb = b => (b / 1024).toFixed(1) + ' KB';
f.onsubmit = async e => {
  e.preventDefault();
  const file = document.getElementById('file').files[0];
  if (!file) { o.textContent = 'Pick a file first.'; return; }
  o.textContent = `Compressing ${file.name} (${kb(file.size)})…`;
  c.innerHTML = '';
  try {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('mode', document.getElementById('mode').value);
    const r = await fetch('/api/compress', { method: 'POST', body: fd });
    if (!r.ok) { o.textContent = `Server error ${r.status}: ${await r.text()}`; return; }
    const j = await r.json();
    o.textContent = JSON.stringify({
      file: j.filename,
      orig: kb(j.orig_size), compressed: kb(j.new_size),
      saving_pct: j.saving_pct, score_10: j.score_10, verdict: j.verdict,
      ssim: j.ssim, psnr: j.psnr, time_ms: j.total_ms,
      params: j.params, explanation: j.explanation
    }, null, 2);
    const isImg = j.kind === 'image';
    const name = j.download.split('/').pop();
    c.innerHTML = `<div><h3>Compressed: ${kb(j.orig_size)} → ${kb(j.new_size)} (${j.saving_pct}% smaller)</h3>` +
      (isImg ? `<img src="${j.download}"/>` : `<video src="${j.download}" controls/>`) +
      `<p><a href="${j.download}" download="${name}">⬇ Download ${name}</a></p></div>`;
  } catch (err) {
    o.textContent = 'Request failed: ' + err.message;
  }
};
