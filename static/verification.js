// Optional verification UI. Workbook comparison rules live in comparison.py.
const verifyPanel = document.querySelector('#verification');
const verifyToggle = document.querySelector('#verify-toggle');
const expectedInput = document.querySelector('#expected');
const compareButton = document.querySelector('#compare-button');
const compareStatus = document.querySelector('#comparison-status');
const compareDetails = document.querySelector('#comparison-details');
let currentWorkbook;
let comparisonRequest;

function resetComparison() {
  if (comparisonRequest) comparisonRequest.abort();
  comparisonRequest = undefined;
  compareStatus.textContent = '';
  compareDetails.replaceChildren();
  compareButton.disabled = false;
  window.dispatchEvent(new CustomEvent('app-busy', { detail: { operation: 'compare', active: false } }));
}
window.addEventListener('result-cleared', () => {
  resetComparison();
  currentWorkbook = undefined;
  expectedInput.value = '';
  verifyPanel.hidden = true;
  verifyToggle.setAttribute('aria-expanded', 'false');
});
window.addEventListener('result-ready', event => { currentWorkbook = event.detail; });
expectedInput.addEventListener('change', resetComparison);
verifyToggle.addEventListener('click', () => {
  verifyPanel.hidden = !verifyPanel.hidden;
  verifyToggle.setAttribute('aria-expanded', String(!verifyPanel.hidden));
  if (!verifyPanel.hidden) expectedInput.focus();
});

function showExamples(title, columns, examples) {
  if (!examples.length) return;
  const heading = document.createElement('h4');
  heading.textContent = `${title} (up to 10 distinct rows)`;
  const wrapper = document.createElement('div');
  wrapper.className = 'table-scroll';
  const table = document.createElement('table');
  const caption = document.createElement('caption');
  caption.textContent = title;
  table.append(caption);
  const header = table.createTHead().insertRow();
  for (const label of [...columns, 'Occurrences']) {
    const cell = document.createElement('th');
    cell.scope = 'col'; cell.textContent = label; header.append(cell);
  }
  const body = table.createTBody();
  for (const example of examples) {
    const row = body.insertRow();
    for (const value of [...example.values, example.count]) row.insertCell().textContent = value;
  }
  wrapper.append(table); compareDetails.append(heading, wrapper);
}

document.querySelector('#verify-form').addEventListener('submit', async event => {
  event.preventDefault(); resetComparison();
  const expected = expectedInput.files[0];
  if (!currentWorkbook || !expected) return;
  if (!expected.name.toLowerCase().endsWith('.xlsx') || expected.size + currentWorkbook.size >= 25 * 1024 * 1024) {
    compareStatus.textContent = 'Choose an .xlsx workbook. Both workbooks together must be less than 25 MB.';
    return;
  }
  const controller = new AbortController(); comparisonRequest = controller;
  const data = new FormData();
  data.append('actual', currentWorkbook, 'consolidated.xlsx');
  data.append('expected', expected);
  compareButton.disabled = true;
  window.dispatchEvent(new CustomEvent('app-busy', { detail: { operation: 'compare', active: true } }));
  compareStatus.textContent = 'Comparing workbooks…';
  try {
    const response = await fetch('/compare', { method: 'POST', body: data, signal: controller.signal });
    const report = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(report.error || 'Comparison failed. Please try again.');
    if (controller !== comparisonRequest) return;
    if (report.missing_columns.length || report.extra_columns.length) {
      compareStatus.textContent = `Column headings differ. Missing from result: ${report.missing_columns.join(', ') || 'none'}. Extra in result: ${report.extra_columns.join(', ') || 'none'}. Row comparison was not performed.`;
    } else {
      compareStatus.textContent = `${report.matches ? 'Results match.' : 'Differences found.'} ${report.matching_rows} matching rows · ${report.missing_rows} missing from result · ${report.extra_rows} extra in result.`;
      showExamples('Missing from result', report.columns, report.missing_examples);
      showExamples('Extra in result', report.columns, report.extra_examples);
    }
  } catch (error) {
    if (controller === comparisonRequest && error.name !== 'AbortError') compareStatus.textContent = error.message;
  } finally {
    if (controller === comparisonRequest) {
      compareButton.disabled = false;
      window.dispatchEvent(new CustomEvent('app-busy', { detail: { operation: 'compare', active: false } }));
    }
  }
});
