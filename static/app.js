const form = document.querySelector('#form');
const input = document.querySelector('#files');
const button = document.querySelector('#submit');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
let downloadUrl;

function clearResult() {
  result.hidden = true;
  if (downloadUrl) URL.revokeObjectURL(downloadUrl);
  downloadUrl = undefined;
  document.querySelector('#download').removeAttribute('href');
}
input.addEventListener('change', () => {
  clearResult();
  status.textContent = '';
  status.className = '';
  const list = document.querySelector('#file-list');
  list.replaceChildren();
  for (const file of input.files) {
    const item = document.createElement('li');
    item.textContent = `${file.name} · ${(file.size / 1024).toFixed(0)} KB`;
    list.append(item);
  }
  button.disabled = input.files.length < 2;
});
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearResult();
  status.className = '';
  const files = [...input.files];
  if (files.length < 2 || files.length > 20 || files.some(file => !file.name.toLowerCase().endsWith('.xlsx')) || files.reduce((sum, file) => sum + file.size, 0) >= 25 * 1024 * 1024) {
    status.className = 'error';
    status.textContent = 'Choose 2–20 .xlsx files totalling less than 25 MB.';
    return;
  }
  const data = new FormData(form);
  button.disabled = true;
  input.disabled = true;
  status.textContent = 'Combining your workbooks…';
  try {
    const response = await fetch('/consolidate', { method: 'POST', body: data });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || 'The request failed. Please try again.');
    }
    downloadUrl = URL.createObjectURL(await response.blob());
    document.querySelector('#download').href = downloadUrl;
    document.querySelector('#summary').textContent = `${response.headers.get('X-File-Count')} files processed · ${Number(response.headers.get('X-Row-Count')).toLocaleString()} rows combined`;
    result.hidden = false;
    status.textContent = 'Consolidation complete. Your download is ready.';
  } catch (error) {
    status.className = 'error';
    status.textContent = error.message || 'Could not connect. Please try again.';
  } finally {
    input.disabled = false;
    button.disabled = input.files.length < 2;
  }
});
