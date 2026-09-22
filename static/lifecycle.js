// Local server control only. The launcher owns process shutdown.
const stopButton = document.querySelector('#stop-app');
const stopStatus = document.querySelector('#stop-status');
const operations = new Set();
window.addEventListener('app-busy', event => {
  if (event.detail.active) operations.add(event.detail.operation);
  else operations.delete(event.detail.operation);
  stopButton.disabled = operations.size > 0;
});
stopButton.addEventListener('click', async () => {
  if (!window.confirm('Stop Excel Consolidator? Download any result you want to keep first.')) return;
  const controls = [...document.querySelectorAll('button, input')];
  const previouslyDisabled = controls.map(control => control.disabled);
  controls.forEach(control => { control.disabled = true; });
  stopStatus.textContent = 'Requesting shutdown…';
  try {
    const response = await fetch('/stop', {
      method: 'POST', headers: { 'X-Stop-Token': document.querySelector('meta[name="local-stop-token"]').content },
      signal: AbortSignal.timeout(10000)
    });
    const report = await response.json();
    if (!response.ok) throw new Error(report.error || 'Shutdown failed.');
    stopStatus.textContent = report.message;
    stopButton.textContent = 'App stopping';
  } catch (error) {
    stopStatus.textContent = `Could not confirm shutdown. ${error.message} You can close the launcher window to stop the app.`;
    controls.forEach((control, index) => { control.disabled = previouslyDisabled[index]; });
  }
});
