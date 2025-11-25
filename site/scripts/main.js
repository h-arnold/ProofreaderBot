// Boilerplate wiring for the GitHub Pages prototype. It wires Papa Parse (CSV) + Arquero (data wrangling) +
// ApexCharts (visuals) with Tailwind-styled controls so the scraper data can be explored in the browser.

import Papa from 'https://cdn.jsdelivr.net/npm/papaparse@5.4.1/+esm';
import * as aq from 'https://cdn.jsdelivr.net/npm/arquero@5.6.3/dist/arquero.mjs';
import ApexCharts from 'https://cdn.jsdelivr.net/npm/apexcharts@3.49.0/dist/apexcharts.esm.js';

const DEFAULT_CSV_URL = './data/sample.csv';

const elements = {
  fileInput: document.getElementById('file-input'),
  remoteCsvForm: document.getElementById('remote-csv-form'),
  remoteCsvUrl: document.getElementById('remote-csv-url'),
  loadSample: document.getElementById('load-sample'),
  dataStatus: document.getElementById('data-status'),
  dimensionSelect: document.getElementById('dimension-select'),
  measureSelect: document.getElementById('measure-select'),
  aggregationSelect: document.getElementById('aggregation-select'),
  sortDescending: document.getElementById('sort-desc'),
  rowCount: document.getElementById('row-count'),
  chartSummary: document.getElementById('chart-summary'),
  chartEl: document.getElementById('chart'),
  table: document.getElementById('data-table'),
  tableHead: document.querySelector('#data-table thead'),
  tableBody: document.querySelector('#data-table tbody'),
  previewInfo: document.getElementById('preview-info'),
  toast: document.getElementById('toast'),
};

const state = {
  table: null,
  aggregatedTable: null,
  categoricalColumns: [],
  numericColumns: [],
  chart: null,
  sourceLabel: 'No dataset loaded',
};

init();

function init() {
  elements.fileInput.addEventListener('change', handleFileUpload);
  elements.remoteCsvForm.addEventListener('submit', handleRemoteCsvSubmit);
  elements.loadSample.addEventListener('click', () => loadCsvFromUrl(DEFAULT_CSV_URL, 'sample dataset'));

  elements.dimensionSelect.addEventListener('change', handleConfigChange);
  elements.measureSelect.addEventListener('change', handleConfigChange);
  elements.aggregationSelect.addEventListener('change', handleConfigChange);
  elements.sortDescending.addEventListener('change', handleConfigChange);

  // Preload the sample data straight away so the template feels alive.
  loadCsvFromUrl(DEFAULT_CSV_URL, 'sample dataset');
}

async function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  try {
    const rows = await parseCsvFile(file);
    ingestRows(rows, file.name);
    showToast(`Loaded ${rows.length} rows from ${file.name}.`);
  } catch (error) {
    console.error(error);
    showToast(`Failed to parse ${file.name}. Check the console for details.`, true);
  } finally {
    event.target.value = '';
  }
}

async function handleRemoteCsvSubmit(event) {
  event.preventDefault();
  const url = elements.remoteCsvUrl.value.trim();
  if (!url) {
    showToast('Enter a CSV URL before fetching.', true);
    return;
  }

  await loadCsvFromUrl(url, url);
}

async function loadCsvFromUrl(url, sourceLabel) {
  updateStatus(`Loading ${sourceLabel}…`);

  try {
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }

    const text = await response.text();
    const rows = parseCsvText(text);
    ingestRows(rows, sourceLabel);
    showToast(`Loaded ${rows.length} rows from ${sourceLabel}.`);
  } catch (error) {
    console.error('Failed to load CSV from URL', error);
    showToast(`Unable to load CSV from ${sourceLabel}. ${error.message}`, true);
    updateStatus('No dataset loaded');
  }
}

function parseCsvFile(file) {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete(result) {
        if (result.errors?.length) {
          reject(result.errors[0]);
          return;
        }
        resolve(result.data);
      },
      error(err) {
        reject(err);
      },
    });
  });
}

function parseCsvText(text) {
  const result = Papa.parse(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });

  if (result.errors?.length) {
    throw result.errors[0];
  }

  return result.data;
}

function ingestRows(rows, sourceLabel) {
  const usableRows = rows.filter((row) => Object.values(row).some((value) => value !== null && value !== undefined && `${value}`.trim() !== ''));
  if (!usableRows.length) {
    throw new Error('The CSV contains no data rows.');
  }

  state.table = aq.from(usableRows);
  state.sourceLabel = sourceLabel;
  classifyColumns();
  populateSelectors();
  elements.rowCount.textContent = `${state.table.numRows().toLocaleString()} rows`;
  updateStatus(`Loaded from ${sourceLabel}`);
  handleConfigChange();
}

function classifyColumns() {
  const numeric = [];
  const categorical = [];

  for (const column of state.table.columnNames()) {
    if (columnLooksNumeric(column)) {
      numeric.push(column);
    } else {
      categorical.push(column);
    }
  }

  state.numericColumns = numeric;
  state.categoricalColumns = categorical;
}

function columnLooksNumeric(columnName) {
  const values = state.table.array(columnName);
  let hasNumericValue = false;

  for (const value of values) {
    if (value === null || value === undefined || value === '') {
      continue;
    }

    if (typeof value === 'number' && Number.isFinite(value)) {
      hasNumericValue = true;
      continue;
    }

    return false;
  }

  return hasNumericValue;
}

function populateSelectors() {
  setSelectOptions(elements.dimensionSelect, state.categoricalColumns, 'Select a dimension…');
  setSelectOptions(elements.measureSelect, state.numericColumns, 'Select a measure…');

  elements.dimensionSelect.disabled = !state.categoricalColumns.length;
  elements.measureSelect.disabled = !state.numericColumns.length;
}

function setSelectOptions(select, options, placeholder) {
  select.innerHTML = '';

  const placeholderOption = document.createElement('option');
  placeholderOption.value = '';
  placeholderOption.textContent = placeholder;
  placeholderOption.disabled = true;
  placeholderOption.selected = true;
  select.appendChild(placeholderOption);

  for (const option of options) {
    const opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option;
    select.appendChild(opt);
  }
}

function handleConfigChange() {
  if (!state.table) {
    return;
  }

  const dimension = elements.dimensionSelect.value;
  const measure = elements.measureSelect.value;

  if (!dimension || (!measure && elements.aggregationSelect.value !== 'count')) {
    clearVisuals('Select a dimension and measure to generate the chart.');
    return;
  }

  const aggregated = buildAggregatedTable({ dimension, measure, aggregation: elements.aggregationSelect.value });
  state.aggregatedTable = aggregated;
  renderChart(aggregated, { dimension, measure });
  renderTablePreview(aggregated, dimension, measure);
  elements.chartSummary.textContent = summariseAggregation(aggregated, dimension, measure);
}

function buildAggregatedTable({ dimension, measure, aggregation }) {
  const aggregations = {
    sum: aq.op.sum(measure),
    average: aq.op.average(measure),
    median: aq.op.median(measure),
    count: aq.op.count(),
    max: aq.op.max(measure),
    min: aq.op.min(measure),
  };

  const rollupExpression = aggregation === 'count' ? { value: aggregations.count } : { value: aggregations[aggregation] };
  const grouped = state.table.groupby(dimension).rollup(rollupExpression);
  const ordered = elements.sortDescending.checked ? grouped.orderby(aq.desc('value')) : grouped.orderby(aq.asc('value'));

  return ordered;
}

function renderChart(table, { dimension, measure }) {
  const categories = table.array(dimension);
  const values = table.array('value');

  const aggregationLabel = elements.aggregationSelect.value === 'count'
    ? 'Row count'
    : `${capitalise(elements.aggregationSelect.value)} of ${measure}`;

  const options = {
    chart: {
      type: 'bar',
      height: 360,
      toolbar: { show: false },
      animations: { enabled: true },
      foreColor: '#475569', // slate-600
      fontFamily: 'Open Sans, sans-serif',
    },
    series: [
      {
        name: aggregationLabel,
        data: values,
      },
    ],
    colors: ['#009fe3'], // WJEC Blue
    xaxis: {
      categories,
      labels: {
        rotateAlways: false,
        style: { fontSize: '12px' },
      },
    },
    yaxis: {
      labels: {
        formatter: (val) => formatNumber(val),
      },
    },
    dataLabels: {
      enabled: false,
    },
    tooltip: {
      theme: 'light',
      y: {
        formatter: (val) => formatNumber(val),
      },
    },
    plotOptions: {
      bar: {
        borderRadius: 4,
        columnWidth: '55%',
      },
    },
    theme: {
      mode: 'light',
    },
  };

  if (!state.chart) {
    state.chart = new ApexCharts(elements.chartEl, options);
    state.chart.render();
  } else {
    state.chart.updateOptions(options, true, true);
  }
}

function renderTablePreview(table, dimension, measure) {
  const rows = table.objects({ limit: 10 });
  const headers = [dimension, 'value'];

  elements.tableHead.innerHTML = '';
  const headRow = document.createElement('tr');
  headers.forEach((header) => {
    const th = document.createElement('th');
    th.scope = 'col';
    th.className = 'px-4 py-3';
    th.textContent = header === 'value' ? aggregationHeader(measure) : header;
    headRow.appendChild(th);
  });
  elements.tableHead.appendChild(headRow);

  elements.tableBody.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50 transition-colors';

    const dimensionCell = document.createElement('td');
    dimensionCell.className = 'whitespace-nowrap px-4 py-3 font-medium text-slate-700';
    dimensionCell.textContent = row[dimension];

    const valueCell = document.createElement('td');
    valueCell.className = 'px-4 py-3 text-slate-600';
    valueCell.textContent = formatNumber(row.value);

    tr.appendChild(dimensionCell);
    tr.appendChild(valueCell);
    elements.tableBody.appendChild(tr);
  });

  elements.previewInfo.textContent = `Previewing ${Math.min(rows.length, 10)} of ${table.numRows()} grouped rows.`;
}

function summariseAggregation(table, dimension, measure) {
  const aggregation = elements.aggregationSelect.value;
  const totalGroups = table.numRows();
  const label = aggregation === 'count' ? 'Row count' : `${capitalise(aggregation)} of ${measure}`;
  return `${label} by ${dimension}. ${totalGroups.toLocaleString()} groups.`;
}

function aggregationHeader(measure) {
  return elements.aggregationSelect.value === 'count'
    ? 'Row count'
    : `${elements.aggregationSelect.options[elements.aggregationSelect.selectedIndex].text} (${measure})`;
}

function clearVisuals(message) {
  elements.chartSummary.textContent = message;
  elements.tableHead.innerHTML = '';
  elements.tableBody.innerHTML = '';
  elements.previewInfo.textContent = 'No preview available yet.';

  if (state.chart) {
    state.chart.updateOptions({ series: [{ data: [] }], xaxis: { categories: [] } }, true, true);
  }
}

function updateStatus(message) {
  elements.dataStatus.textContent = message;
}

function showToast(message, isError = false) {
  const toast = document.createElement('div');
  toast.className = `pointer-events-auto inline-flex items-center gap-3 rounded-xl border px-4 py-3 text-sm shadow-lg transition ${
    isError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-brand/20 bg-brand-light text-brand-dark'
  }`;
  toast.textContent = message;

  elements.toast.innerHTML = '';
  elements.toast.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('opacity-0');
  }, 3600);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.parentElement.removeChild(toast);
    }
  }, 4200);
}

function capitalise(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatNumber(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return value;
  }
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}
