/**
 * FIPE Price Tracker - Frontend JavaScript
 * 
 * This file handles all the interactive functionality:
 * - Loading data from the API
 * - Updating cascading dropdowns
 * - Rendering the Plotly chart
 * - Calculating statistics
 */

// Global variables to store state
let availableMonths = [];
let currentChartData = null;
let vehicleOptions = null;  // Stores all models and years for bidirectional filtering

// Multi-vehicle comparison state
let selectedVehicles = [];
const MAX_VEHICLES = 5;
let currentDateRange = { startDate: null, endDate: null }; // Track the actual date range used for fetched data

// Color palette for different vehicles
const VEHICLE_COLORS = [
    '#2563eb', // Blue
    '#10b981', // Green
    '#f59e0b', // Amber
    '#ef4444', // Red
    '#8b5cf6'  // Purple
];

/**
 * Get CSRF token from meta tag for form submissions
 * @returns {string} CSRF token
 */
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

/**
 * Format a number as Brazilian currency (R$ 1.234,56)
 */
function formatBRL(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Format year description - convert 32000 to "Zero KM"
 */
function formatYearDescription(yearDesc) {
    if (!yearDesc) return yearDesc;

    // Check if year description starts with 32000
    if (yearDesc.startsWith('32000')) {
        // Replace 32000 with "Zero KM" while keeping the fuel type
        return yearDesc.replace('32000', 'Zero KM');
    }

    return yearDesc;
}

/**
 * Calculate depreciation metrics for a vehicle
 * @param {Array} priceData - Array of {date, price, label} objects
 * @param {string} startDate - ISO date string (e.g., "2020-01-01")
 * @param {string} endDate - ISO date string (e.g., "2024-12-01")
 * @returns {Object} Depreciation metrics
 */
function calculateDepreciationMetrics(priceData, startDate, endDate) {
    if (!priceData || priceData.length < 2) {
        return null;
    }

    const prices = priceData.map(d => d.price);
    const firstPrice = prices[0];
    const lastPrice = prices[prices.length - 1];

    // Calculate total depreciation
    const totalDepreciation = ((lastPrice - firstPrice) / firstPrice) * 100;

    // Calculate time elapsed
    const start = new Date(startDate);
    const end = new Date(endDate);
    const monthsElapsed = (end.getFullYear() - start.getFullYear()) * 12
                         + (end.getMonth() - start.getMonth());
    const yearsElapsed = monthsElapsed / 12;

    // Calculate average annual depreciation
    const annualDepreciation = yearsElapsed > 0
        ? totalDepreciation / yearsElapsed
        : totalDepreciation;

    // Calculate monthly depreciation (last month vs previous month)
    let monthlyDepreciation = 0;
    if (prices.length >= 2) {
        const lastMonth = prices[prices.length - 1];
        const previousMonth = prices[prices.length - 2];
        monthlyDepreciation = ((lastMonth - previousMonth) / previousMonth) * 100;
    }

    return {
        total: totalDepreciation,
        annual: annualDepreciation,
        monthly: monthlyDepreciation,
        monthsElapsed: monthsElapsed,
        yearsElapsed: yearsElapsed,
        firstPrice: firstPrice,
        lastPrice: lastPrice
    };
}

/**
 * Calculate yearly depreciation breakdown
 * @param {Array} priceData - Array of {date, price, label} objects
 * @returns {Array} Array of {year, rate, startDate, endDate, startPrice, endPrice}
 */
function calculateYearlyBreakdown(priceData) {
    if (!priceData || priceData.length < 2) {
        return [];
    }

    // Group data points by calendar year
    const yearGroups = {};
    priceData.forEach(point => {
        const year = new Date(point.date).getFullYear();
        if (!yearGroups[year]) {
            yearGroups[year] = [];
        }
        yearGroups[year].push(point);
    });

    // Calculate depreciation for each year
    const breakdown = [];
    Object.keys(yearGroups).sort().forEach(year => {
        const yearData = yearGroups[year];
        if (yearData.length < 2) return; // Skip years with insufficient data

        const firstPoint = yearData[0];
        const lastPoint = yearData[yearData.length - 1];
        const rate = ((lastPoint.price - firstPoint.price) / firstPoint.price) * 100;

        breakdown.push({
            year: parseInt(year),
            rate: rate,
            startDate: firstPoint.date,
            endDate: lastPoint.date,
            startLabel: firstPoint.label,
            endLabel: lastPoint.label,
            startPrice: firstPoint.price,
            endPrice: lastPoint.price
        });
    });

    return breakdown;
}

/**
 * Calculate real (inflation-adjusted) depreciation
 * @param {number} nominalRate - Nominal depreciation rate (%)
 * @param {number} ipcaRate - IPCA inflation rate (%)
 * @returns {number} Real depreciation rate (%)
 */
function calculateRealDepreciation(nominalRate, ipcaRate) {
    if (ipcaRate === null || ipcaRate === undefined) {
        return null;
    }
    // Real rate = ((1 + nominal) / (1 + inflation)) - 1
    const nominal = nominalRate / 100;
    const ipca = ipcaRate / 100;
    const real = ((1 + nominal) / (1 + ipca) - 1) * 100;
    return real;
}

/**
 * Format percentage in Brazilian style (comma as decimal separator)
 * @param {number} value - Percentage value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage (e.g., "-8,5%")
 */
function formatPercentageBrazilian(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }

    const sign = value > 0 ? '+' : '';
    const formatted = value.toFixed(decimals).replace('.', ',');
    return `${sign}${formatted}%`;
}

/**
 * Render depreciation section HTML
 * @param {Object} vehicle - Vehicle object with data
 * @param {Object} metrics - Depreciation metrics from calculateDepreciationMetrics
 * @param {Object} indicators - Economic indicators {ipca, cdi}
 * @param {Array} yearlyBreakdown - Yearly breakdown from calculateYearlyBreakdown
 * @returns {string} HTML string for depreciation section
 */
function renderDepreciationSection(vehicle, metrics, indicators, yearlyBreakdown) {
    if (!metrics) {
        return `
            <div class="depreciation-section">
                <div class="depreciation-header">
                    <i class="bi bi-graph-down"></i>
                    Taxa de Depreciação
                </div>
                <p class="text-muted small">Dados insuficientes para calcular depreciação</p>
            </div>
        `;
    }

    // Calculate real depreciation if IPCA is available
    let realDepreciationHtml = '';
    if (indicators.ipca !== null) {
        const realRate = calculateRealDepreciation(metrics.total, indicators.ipca);
        // If real rate > 0: vehicle gained purchasing power (beat inflation)
        // If real rate < 0: vehicle lost purchasing power (worse than inflation)
        const comparison = realRate > 0 ? 'melhor' : 'pior';
        realDepreciationHtml = `
            <div class="depreciation-real-comparison">
                <span class="small text-muted">
                    Real: ${formatPercentageBrazilian(realRate, 2)}
                    (${comparison} que inflação)
                </span>
            </div>
        `;
    }

    // Build yearly breakdown HTML
    let yearlyHtml = '';
    if (yearlyBreakdown.length > 0) {
        yearlyHtml = `
            <div class="depreciation-yearly-breakdown">
                <div class="depreciation-subheader">
                    <i class="bi bi-calendar3"></i>
                    Detalhamento por Ano
                </div>
                <ul class="depreciation-yearly-list">
                    ${yearlyBreakdown.map(year => `
                        <li>
                            <strong>${year.year}:</strong>
                            <span class="depreciation-rate ${year.rate < 0 ? 'negative' : 'positive'}">
                                ${formatPercentageBrazilian(year.rate, 1)}
                            </span>
                            <span class="small text-muted">
                                (${year.startLabel} - ${year.endLabel})
                            </span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    return `
        <div class="depreciation-section">
            <div class="depreciation-header">
                <i class="bi bi-graph-down"></i>
                Taxa de Depreciação
            </div>

            <div class="depreciation-metrics-grid">
                <div class="depreciation-metric-card">
                    <div class="depreciation-metric-label">Anual Média</div>
                    <div class="depreciation-metric-value ${metrics.annual < 0 ? 'negative' : 'positive'}">
                        ${formatPercentageBrazilian(metrics.annual, 1)}/ano
                    </div>
                    <div class="depreciation-metric-detail">
                        ${Math.round(metrics.monthsElapsed)} meses
                    </div>
                </div>

                <div class="depreciation-metric-card">
                    <div class="depreciation-metric-label">Mensal</div>
                    <div class="depreciation-metric-value ${metrics.monthly < 0 ? 'negative' : 'positive'}">
                        ${formatPercentageBrazilian(metrics.monthly, 1)}/mês
                    </div>
                    <div class="depreciation-metric-detail">
                        Último mês
                    </div>
                </div>

                <div class="depreciation-metric-card">
                    <div class="depreciation-metric-label">Total</div>
                    <div class="depreciation-metric-value ${metrics.total < 0 ? 'negative' : 'positive'}">
                        ${formatPercentageBrazilian(metrics.total, 1)}
                    </div>
                    <div class="depreciation-metric-detail">
                        Todo período
                    </div>
                </div>
            </div>

            ${realDepreciationHtml}
            ${yearlyHtml}
        </div>
    `;
}

/**
 * Get theme-aware colors for Plotly charts
 */
function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    return {
        paper_bgcolor: isDark ? '#1e293b' : '#ffffff',
        plot_bgcolor: isDark ? '#1e293b' : '#eff6ff',
        gridcolor: isDark ? '#334155' : '#dbeafe',
        linecolor: isDark ? '#475569' : '#93c5fd',
        textcolor: isDark ? '#ffffff' : '#1e3a8a',
        titlecolor: isDark ? '#ffffff' : '#111827',
        hoverlabel_bgcolor: isDark ? '#0f172a' : '#111827'
    };
}

/**
 * Show loading spinner and hide chart
 */
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('priceChart').style.display = 'none';
    document.getElementById('errorMessage').classList.add('d-none');
}

/**
 * Hide loading spinner and show chart
 */
function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('priceChart').style.display = 'block';
}

/**
 * Show error message
 */
function showError(message) {
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('priceChart').style.display = 'none';
    document.getElementById('errorText').textContent = message;
    document.getElementById('errorMessage').classList.remove('d-none');
}

/**
 * Add vehicle to comparison list
 */
async function addVehicle() {
    const brandSelect = document.getElementById('brandSelect');
    const modelSelect = document.getElementById('modelSelect');
    const yearSelect = document.getElementById('yearSelect');

    // Validate all selections are made
    if (!brandSelect.value || brandSelect.value === '') {
        alert('Por favor, selecione uma marca');
        return;
    }

    if (!modelSelect.value || modelSelect.value === '') {
        alert('Por favor, selecione um modelo');
        return;
    }

    if (!yearSelect.value || yearSelect.value === '') {
        alert('Por favor, selecione um ano/combustível');
        return;
    }

    const modelId = modelSelect.value;
    const yearDesc = yearSelect.value;
    const brandName = brandSelect.options[brandSelect.selectedIndex].text;
    const modelName = modelSelect.options[modelSelect.selectedIndex].text;

    // Look up the correct ModelYear ID from the mapping
    let yearId;
    if (vehicleOptions && vehicleOptions.model_year_lookup) {
        const modelIdStr = String(modelId);
        yearId = vehicleOptions.model_year_lookup[modelIdStr]?.[yearDesc];

        if (!yearId) {
            alert('Erro: combinação de modelo e ano inválida');
            console.error('Could not find year_id for model:', modelId, 'year:', yearDesc);
            return;
        }
    } else {
        // Fallback for legacy mode (shouldn't happen in normal operation)
        yearId = parseInt(yearSelect.value);
    }

    // Check if already added
    if (selectedVehicles.some(v => v.id === yearId)) {
        alert('Este veículo já está na comparação');
        return;
    }

    // Check max vehicles
    if (selectedVehicles.length >= MAX_VEHICLES) {
        alert(`Máximo de ${MAX_VEHICLES} veículos permitidos para comparação`);
        return;
    }

    // Add to list
    const vehicle = {
        id: yearId,
        brand: brandName,
        model: modelName,
        year: yearDesc,
        color: VEHICLE_COLORS[selectedVehicles.length]
    };

    selectedVehicles.push(vehicle);
    updateVehiclesUI();
    updateButtonsState();

    // Auto-update chart when adding vehicle
    await updateComparisonChart();
}

/**
 * Remove vehicle from comparison list
 */
function removeVehicle(vehicleId) {
    selectedVehicles = selectedVehicles.filter(v => v.id !== vehicleId);

    // Reassign colors
    selectedVehicles.forEach((vehicle, index) => {
        vehicle.color = VEHICLE_COLORS[index];
    });

    updateVehiclesUI();
    updateButtonsState();

    // Update chart if there are still vehicles
    if (selectedVehicles.length > 0) {
        updateComparisonChart();
    } else {
        // Clear the chart
        document.getElementById('carInfo').classList.add('d-none');
        Plotly.purge('priceChart');
        clearStatistics();
    }
}

/**
 * Update the vehicles list UI
 */
function updateVehiclesUI() {
    const container = document.getElementById('selectedVehicles');
    const countSpan = document.getElementById('vehicleCount');
    const listDiv = document.getElementById('vehiclesList');

    countSpan.textContent = selectedVehicles.length;

    if (selectedVehicles.length === 0) {
        listDiv.classList.add('d-none');
        return;
    }

    listDiv.classList.remove('d-none');
    container.innerHTML = '';

    selectedVehicles.forEach(vehicle => {
        const chip = document.createElement('div');
        chip.className = 'vehicle-chip';
        chip.innerHTML = `
            <div class="vehicle-chip-info">
                <div class="vehicle-chip-color" style="background-color: ${vehicle.color}"></div>
                <div class="vehicle-chip-text">
                    <div class="vehicle-chip-name">${vehicle.brand} ${vehicle.model}</div>
                    <div class="vehicle-chip-details">${formatYearDescription(vehicle.year)}</div>
                </div>
            </div>
            <button class="vehicle-chip-remove" onclick="removeVehicle(${vehicle.id})" title="Remover">
                <i class="bi bi-x-circle-fill"></i>
            </button>
        `;
        container.appendChild(chip);
    });
}

/**
 * Update button states
 */
function updateButtonsState() {
    const addBtn = document.getElementById('addVehicle');
    const updateBtn = document.getElementById('updateChart');
    const yearSelect = document.getElementById('yearSelect');

    // Enable add button if year is selected and not at max
    if (yearSelect.value && selectedVehicles.length < MAX_VEHICLES) {
        addBtn.disabled = false;
    } else {
        addBtn.disabled = true;
    }

    // Enable update button if at least one vehicle is selected
    if (selectedVehicles.length > 0) {
        updateBtn.disabled = false;
    } else {
        updateBtn.disabled = true;
    }
}

/**
 * Clear statistics display
 */
function clearStatistics() {
    document.getElementById('currentPrice').textContent = '-';
    document.getElementById('minPrice').textContent = '-';
    document.getElementById('maxPrice').textContent = '-';
    document.getElementById('priceChange').textContent = '-';
}

/**
 * Load all brands from the API
 */
async function loadBrands() {
    try {
        const response = await fetch('/api/brands', {
            credentials: 'same-origin'
        });
        const brands = await response.json();
        
        const brandSelect = document.getElementById('brandSelect');
        brandSelect.innerHTML = '<option value="">Selecione uma marca</option>';
        
        brands.forEach(brand => {
            const option = document.createElement('option');
            option.value = brand.id;
            option.textContent = brand.name;
            brandSelect.appendChild(option);
        });
        
        return brands;
    } catch (error) {
        console.error('Error loading brands:', error);
        showError('Erro ao carregar marcas');
    }
}

/**
 * Load vehicle options for bidirectional filtering
 * This fetches all models and years for a brand at once
 */
async function loadVehicleOptions(brandId) {
    try {
        const response = await fetch(`/api/vehicle-options/${brandId}`, {
            credentials: 'same-origin'
        });
        vehicleOptions = await response.json();

        // Populate both dropdowns with all options
        populateModelDropdown(vehicleOptions.models);
        populateYearDropdown(vehicleOptions.year_descriptions);

        // Enable both dropdowns (bidirectional selection)
        document.getElementById('modelSelect').disabled = false;
        document.getElementById('yearSelect').disabled = false;

        return vehicleOptions;
    } catch (error) {
        console.error('Error loading vehicle options:', error);
        showError('Erro ao carregar opções de veículos');
    }
}

/**
 * Populate the model dropdown with given models
 */
function populateModelDropdown(models, selectedModelId = null) {
    const modelSelect = document.getElementById('modelSelect');
    modelSelect.innerHTML = '<option value="">Selecione um modelo</option>';

    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        modelSelect.appendChild(option);
    });

    if (selectedModelId) {
        modelSelect.value = selectedModelId;
    }
}

/**
 * Populate the year dropdown with given year descriptions
 */
function populateYearDropdown(yearDescriptions, selectedYearDesc = null) {
    const yearSelect = document.getElementById('yearSelect');
    yearSelect.innerHTML = '<option value="">Selecione um ano/combustível</option>';

    yearDescriptions.forEach(yearDesc => {
        const option = document.createElement('option');
        option.value = yearDesc;
        option.textContent = formatYearDescription(yearDesc);
        yearSelect.appendChild(option);
    });

    if (selectedYearDesc) {
        yearSelect.value = selectedYearDesc;
    }
}

/**
 * Filter year dropdown based on selected model
 */
function filterYearsByModel(modelId) {
    if (!vehicleOptions || !modelId) return;

    const modelIdStr = String(modelId);
    const availableYears = vehicleOptions.model_to_years[modelIdStr] || [];

    // Get currently selected year
    const yearSelect = document.getElementById('yearSelect');
    const currentYearValue = yearSelect.value;

    // Repopulate with filtered years
    populateYearDropdown(availableYears);

    // If previously selected year is still valid, keep it selected
    if (currentYearValue && availableYears.includes(currentYearValue)) {
        yearSelect.value = currentYearValue;
    }
}

/**
 * Filter model dropdown based on selected year
 */
function filterModelsByYear(yearDesc) {
    if (!vehicleOptions || !yearDesc) return;

    const availableModelIds = vehicleOptions.year_to_models[yearDesc] || [];

    // Get currently selected model
    const modelSelect = document.getElementById('modelSelect');
    const currentModelId = parseInt(modelSelect.value);

    // Build filtered models list
    const filteredModels = vehicleOptions.models.filter(
        model => availableModelIds.includes(model.id)
    );

    // Repopulate with filtered models
    populateModelDropdown(filteredModels);

    // If previously selected model is still valid, keep it selected
    if (currentModelId && availableModelIds.includes(currentModelId)) {
        modelSelect.value = currentModelId;
    }
}

/**
 * Legacy function - kept for backwards compatibility with default car loading
 * Loads models for a specific brand (old API)
 */
async function loadModels(brandId) {
    // This function is deprecated in favor of loadVehicleOptions
    // but kept for potential legacy code or default car loading
    try {
        const response = await fetch(`/api/models/${brandId}`, {
            credentials: 'same-origin'
        });
        const models = await response.json();

        const modelSelect = document.getElementById('modelSelect');
        modelSelect.innerHTML = '<option value="">Selecione um modelo</option>';
        modelSelect.disabled = false;

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            modelSelect.appendChild(option);
        });

        // Reset year dropdown
        const yearSelect = document.getElementById('yearSelect');
        yearSelect.innerHTML = '<option value="">Selecione um ano/combustível</option>';
        yearSelect.disabled = true;

        return models;
    } catch (error) {
        console.error('Error loading models:', error);
        showError('Erro ao carregar modelos');
    }
}

/**
 * Legacy function - kept for backwards compatibility with default car loading
 * Loads years for a specific model (old API)
 */
async function loadYears(modelId) {
    // This function is deprecated in favor of loadVehicleOptions
    // but kept for potential legacy code or default car loading
    try {
        const response = await fetch(`/api/years/${modelId}`, {
            credentials: 'same-origin'
        });
        const years = await response.json();

        const yearSelect = document.getElementById('yearSelect');
        yearSelect.innerHTML = '<option value="">Selecione um ano</option>';
        yearSelect.disabled = false;

        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year.id;
            option.textContent = year.description;
            yearSelect.appendChild(option);
        });

        return years;
    } catch (error) {
        console.error('Error loading years:', error);
        showError('Erro ao carregar anos');
    }
}

/**
 * Load available months from the database
 *
 * @param {number|null} yearId - Optional year_id to filter months for a specific vehicle
 */
async function loadMonths(yearId = null) {
    try {
        // Build URL with optional year_id parameter
        const url = yearId ? `/api/months?year_id=${yearId}` : '/api/months';
        const response = await fetch(url, {
            credentials: 'same-origin'
        });
        availableMonths = await response.json();

        const startMonthSelect = document.getElementById('startMonth');
        const endMonthSelect = document.getElementById('endMonth');

        // Clear existing options
        startMonthSelect.innerHTML = '';
        endMonthSelect.innerHTML = '';

        // Add all months to both dropdowns
        availableMonths.forEach(month => {
            const startOption = document.createElement('option');
            startOption.value = month.date;
            startOption.textContent = month.label;
            startMonthSelect.appendChild(startOption);

            const endOption = document.createElement('option');
            endOption.value = month.date;
            endOption.textContent = month.label;
            endMonthSelect.appendChild(endOption);
        });

        // Set default date range (first to last month available for this vehicle)
        if (availableMonths.length > 0) {
            startMonthSelect.value = availableMonths[0].date;
            endMonthSelect.value = availableMonths[availableMonths.length - 1].date;
            startMonthSelect.disabled = false;
            endMonthSelect.disabled = false;
        }

        return availableMonths;
    } catch (error) {
        console.error('Error loading months:', error);
        showError('Erro ao carregar meses disponíveis');
    }
}

/**
 * Fetch and display comparison chart data for multiple vehicles
 */
async function updateComparisonChart() {
    const startDate = document.getElementById('startMonth').value;
    const endDate = document.getElementById('endMonth').value;

    // Validate date range
    if (!startDate || !endDate) {
        alert('Por favor, selecione o período');
        return;
    }

    if (new Date(startDate) > new Date(endDate)) {
        alert('O mês inicial deve ser anterior ao mês final');
        return;
    }

    // Check if we have vehicles to compare
    if (selectedVehicles.length === 0) {
        alert('Por favor, adicione pelo menos um veículo para comparar');
        return;
    }

    showLoading();

    try {
        const vehicleIds = selectedVehicles.map(v => v.id);

        const response = await fetch('/api/compare-vehicles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                vehicle_ids: vehicleIds,
                start_date: startDate,
                end_date: endDate
            })
        });

        if (!response.ok) {
            throw new Error('Erro ao buscar dados de comparação');
        }

        const data = await response.json();

        // Update vehicle info with actual data
        data.vehicles.forEach(vehicleData => {
            const vehicle = selectedVehicles.find(v => v.id === vehicleData.id);
            if (vehicle) {
                vehicle.data = vehicleData.data;
            }
        });

        // Store the actual date range used for this data fetch
        currentDateRange = { startDate, endDate };

        // Display comparison info
        displayComparisonInfo();

        // Render the comparison chart
        renderComparisonChart();

        // Update statistics for comparison
        updateComparisonStatistics();

        hideLoading();
    } catch (error) {
        console.error('Error updating comparison chart:', error);
        showError('Erro ao carregar dados de comparação. Verifique sua seleção.');
    }
}

/**
 * Legacy function - redirects to comparison chart
 */
async function updateChart() {
    await updateComparisonChart();
}

/**
 * Display comparison information banner
 */
function displayComparisonInfo() {
    const carInfoDiv = document.getElementById('carInfo');
    const titleSpan = document.getElementById('carInfoTitle');
    const detailsP = document.getElementById('carInfoDetails');

    const count = selectedVehicles.length;
    titleSpan.textContent = `Comparando ${count} ${count === 1 ? 'veículo' : 'veículos'}`;
    detailsP.textContent = selectedVehicles.map(v => `${v.brand} ${v.model} (${formatYearDescription(v.year)})`).join(' • ');

    carInfoDiv.classList.remove('d-none');
}

/**
 * Display car information banner (legacy - for single vehicle)
 */
function displayCarInfo(carInfo) {
    const carInfoDiv = document.getElementById('carInfo');
    const titleSpan = document.getElementById('carInfoTitle');
    const detailsP = document.getElementById('carInfoDetails');

    titleSpan.textContent = `${carInfo.brand} ${carInfo.model}`;
    detailsP.textContent = `Ano/Combustível: ${formatYearDescription(carInfo.year)}`;

    carInfoDiv.classList.remove('d-none');
}

/**
 * Render the Plotly chart with premium styling
 */
function renderChart(data) {
    // Prepare data for Plotly
    // Use ISO date strings for x-axis to ensure chronological ordering
    const dates = data.map(d => d.date);
    const labels = data.map(d => d.label);
    const prices = data.map(d => d.price);

    // Create gradient for the area under the line
    const trace = {
        x: dates,
        y: prices,
        customdata: labels,  // Store Portuguese labels for hover text
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Preço',
        line: {
            color: '#2563eb',
            width: 3,
            shape: 'spline',
            smoothing: 0.8
        },
        marker: {
            size: 8,
            color: '#2563eb',
            line: {
                color: '#fff',
                width: 2
            }
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(37, 99, 235, 0.08)',
        hovertemplate: '<b>%{customdata}</b><br>' +
                      'Preço: R$ %{y:,.2f}<br>' +
                      '<extra></extra>'
    };

    // Get theme-aware colors
    const colors = getChartColors();

    // Premium layout configuration
    const layout = {
        autosize: true,
        title: {
            text: 'Evolução do Preço FIPE',
            font: {
                size: 24,
                family: 'Inter, -apple-system, sans-serif',
                weight: 700,
                color: colors.titlecolor
            },
            pad: {
                t: 10,
                b: 10
            }
        },
        xaxis: {
            title: {
                text: 'Período',
                font: {
                    size: 14,
                    family: 'Inter, -apple-system, sans-serif',
                    weight: 600,
                    color: colors.textcolor
                }
            },
            type: 'date',  // Treat x values as dates for proper chronological ordering
            tickangle: -45,
            automargin: true,
            nticks: 15,  // Limit number of tick marks to prevent overcrowding
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: colors.textcolor
            },
            gridcolor: colors.gridcolor,
            gridwidth: 1,
            showline: true,
            linecolor: colors.linecolor,
            linewidth: 2
        },
        yaxis: {
            title: {
                text: 'Preço (R$)',
                font: {
                    size: 14,
                    family: 'Inter, -apple-system, sans-serif',
                    weight: 600,
                    color: colors.textcolor
                }
            },
            tickformat: ',.0f',
            automargin: true,
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: colors.textcolor
            },
            gridcolor: colors.gridcolor,
            gridwidth: 1,
            showline: true,
            linecolor: colors.linecolor,
            linewidth: 2,
            zeroline: false
        },
        hovermode: 'x unified',
        plot_bgcolor: colors.plot_bgcolor,
        paper_bgcolor: colors.paper_bgcolor,
        margin: {
            l: 80,
            r: 40,
            t: 100,
            b: 120
        },
        hoverlabel: {
            bgcolor: colors.hoverlabel_bgcolor,
            bordercolor: '#2563eb',
            font: {
                size: 14,
                family: 'Inter, -apple-system, sans-serif',
                color: 'white'
            }
        }
    };

    // Configuration options
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        toImageButtonOptions: {
            format: 'png',
            filename: 'fipe_price_chart',
            height: 600,
            width: 1200,
            scale: 2
        }
    };

    // Render the chart with animation
    Plotly.newPlot('priceChart', [trace], layout, config).then(() => {
        // Animate the chart on render
        Plotly.animate('priceChart', {
            data: [trace],
            traces: [0],
            layout: {}
        }, {
            transition: {
                duration: 800,
                easing: 'cubic-in-out'
            },
            frame: {
                duration: 800
            }
        });
    });
}

/**
 * Convert prices to base 100 indexed values
 */
function convertToBase100(prices) {
    if (!prices || prices.length === 0) return [];
    const basePrice = prices[0];
    return prices.map(price => (price / basePrice) * 100);
}

/**
 * Render comparison chart with multiple vehicle traces
 */
function renderComparisonChart() {
    const chartType = document.getElementById('chartType').value;
    const isBase100 = chartType === 'base100';

    // Create traces for each vehicle
    const traces = selectedVehicles.map((vehicle, index) => {
        if (!vehicle.data || vehicle.data.length === 0) return null;

        // Use ISO date strings for x-axis to ensure chronological ordering
        const dates = vehicle.data.map(d => d.date);
        const labels = vehicle.data.map(d => d.label);
        const prices = vehicle.data.map(d => d.price);

        // Convert to base 100 if needed
        const yValues = isBase100 ? convertToBase100(prices) : prices;

        // Different hover templates based on chart type
        // Use customdata to pass Portuguese labels to hover text
        const hovertemplate = isBase100
            ? '<b>%{fullData.name}</b><br>' +
              '%{customdata}<br>' +
              'Índice: %{y:.2f}<br>' +
              '<extra></extra>'
            : '<b>%{fullData.name}</b><br>' +
              '%{customdata}<br>' +
              'Preço: R$ %{y:,.2f}<br>' +
              '<extra></extra>';

        return {
            x: dates,
            y: yValues,
            customdata: labels,  // Store Portuguese labels for hover text
            type: 'scatter',
            mode: 'lines+markers',
            name: `${vehicle.brand} ${vehicle.model}`,
            line: {
                color: vehicle.color,
                width: 3,
                shape: 'spline',
                smoothing: 0.8
            },
            marker: {
                size: 8,
                color: vehicle.color,
                line: {
                    color: '#fff',
                    width: 2
                }
            },
            hovertemplate: hovertemplate
        };
    }).filter(trace => trace !== null);

    // Get theme-aware colors
    const colors = getChartColors();

    // Premium layout configuration
    const layout = {
        autosize: true,
        title: {
            text: isBase100 ? 'Comparação de Preços FIPE (Base 100)' : 'Comparação de Preços FIPE',
            font: {
                size: 24,
                family: 'Inter, -apple-system, sans-serif',
                weight: 700,
                color: colors.titlecolor
            },
            pad: {
                t: 10,
                b: 10
            }
        },
        xaxis: {
            title: {
                text: 'Período',
                font: {
                    size: 14,
                    family: 'Inter, -apple-system, sans-serif',
                    weight: 600,
                    color: colors.textcolor
                }
            },
            type: 'date',  // Treat x values as dates for proper chronological ordering
            tickangle: -45,
            automargin: true,
            nticks: 15,  // Limit number of tick marks to prevent overcrowding
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: colors.textcolor
            },
            gridcolor: colors.gridcolor,
            gridwidth: 1,
            showline: true,
            linecolor: colors.linecolor,
            linewidth: 2
        },
        yaxis: {
            title: {
                text: isBase100 ? 'Índice (Base 100)' : 'Preço (R$)',
                font: {
                    size: 14,
                    family: 'Inter, -apple-system, sans-serif',
                    weight: 600,
                    color: colors.textcolor
                }
            },
            tickformat: isBase100 ? ',.2f' : ',.0f',
            automargin: true,
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: colors.textcolor
            },
            gridcolor: colors.gridcolor,
            gridwidth: 1,
            showline: true,
            linecolor: colors.linecolor,
            linewidth: 2,
            zeroline: false
        },
        hovermode: 'x unified',
        plot_bgcolor: colors.plot_bgcolor,
        paper_bgcolor: colors.paper_bgcolor,
        margin: {
            l: 80,
            r: 40,
            t: 100,
            b: 120
        },
        hoverlabel: {
            bgcolor: colors.hoverlabel_bgcolor,
            font: {
                size: 14,
                family: 'Inter, -apple-system, sans-serif',
                color: 'white'
            }
        },
        legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: -0.3,
            xanchor: 'center',
            x: 0.5,
            font: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: colors.textcolor
            }
        }
    };

    // Configuration options
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        toImageButtonOptions: {
            format: 'png',
            filename: 'fipe_comparison_chart',
            height: 600,
            width: 1200,
            scale: 2
        }
    };

    // Render the chart
    Plotly.newPlot('priceChart', traces, layout, config).then(() => {
        // Force resize to container width after initial render
        window.requestAnimationFrame(() => {
            Plotly.Plots.resize('priceChart');
        });
    });
}

/**
 * Format a date range in Portuguese (short format)
 * @param {string} startDate - ISO date string (e.g., "2020-01-01")
 * @param {string} endDate - ISO date string (e.g., "2024-12-01")
 * @returns {string} Formatted range (e.g., "jan/2020 - dez/2024")
 */
function formatDateRangeShort(startDate, endDate) {
    if (!startDate || !endDate) return '';

    const monthsShort = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

    const start = new Date(startDate);
    const end = new Date(endDate);

    const startMonth = monthsShort[start.getMonth()];
    const startYear = start.getFullYear();
    const endMonth = monthsShort[end.getMonth()];
    const endYear = end.getFullYear();

    return `${startMonth}/${startYear} - ${endMonth}/${endYear}`;
}

/**
 * Fetch economic indicators from API
 */
async function fetchEconomicIndicators(startDate, endDate) {
    try {
        const response = await fetch('/api/economic-indicators', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate
            })
        });

        if (!response.ok) {
            throw new Error('Failed to fetch economic indicators');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching economic indicators:', error);
        return { ipca: null, cdi: null };
    }
}

/**
 * Update statistics for comparison view - creates individual cards for each vehicle
 */
async function updateComparisonStatistics() {
    if (selectedVehicles.length === 0) return;

    const chartType = document.getElementById('chartType').value;
    const isBase100 = chartType === 'base100';
    const container = document.getElementById('vehicleStatsContainer');
    container.innerHTML = '';

    // Process each vehicle and fetch its specific economic indicators
    for (const [index, vehicle] of selectedVehicles.entries()) {
        if (!vehicle.data || vehicle.data.length === 0) continue;

        const prices = vehicle.data.map(d => d.price);
        const currentPrice = prices[prices.length - 1];
        const firstPrice = prices[0];
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const priceChange = ((currentPrice - firstPrice) / firstPrice) * 100;

        // Get this vehicle's actual date range from its data
        const vehicleStartDate = vehicle.data[0].date;
        const vehicleEndDate = vehicle.data[vehicle.data.length - 1].date;

        // Fetch economic indicators for THIS vehicle's specific date range
        const indicators = await fetchEconomicIndicators(vehicleStartDate, vehicleEndDate);

        // Format the period for display
        const periodLabel = formatDateRangeShort(vehicleStartDate, vehicleEndDate);

        // Calculate depreciation metrics
        const depreciationMetrics = calculateDepreciationMetrics(
            vehicle.data,
            vehicleStartDate,
            vehicleEndDate
        );

        // Calculate yearly breakdown
        const yearlyBreakdown = calculateYearlyBreakdown(vehicle.data);

        // Calculate base 100 values if needed
        let displayValues;
        if (isBase100) {
            const base100Values = convertToBase100(prices);
            displayValues = {
                current: base100Values[base100Values.length - 1],
                min: Math.min(...base100Values),
                max: Math.max(...base100Values),
                format: (val) => val.toFixed(2)
            };
        } else {
            displayValues = {
                current: currentPrice,
                min: minPrice,
                max: maxPrice,
                format: formatBRL
            };
        }

        // Create vehicle stats card
        const card = document.createElement('div');
        card.className = 'vehicle-stats-card';
        card.style.borderLeftColor = vehicle.color;
        card.style.animationDelay = `${index * 0.1}s`;

        card.innerHTML = `
            <div class="vehicle-stats-header">
                <div class="vehicle-stats-color-indicator" style="background-color: ${vehicle.color}"></div>
                <h3 class="vehicle-stats-title">${vehicle.brand} ${vehicle.model} (${formatYearDescription(vehicle.year)})</h3>
            </div>
            <div class="vehicle-stats-grid">
                <div class="vehicle-stat-item">
                    <div class="vehicle-stat-label">${isBase100 ? 'Índice Atual' : 'Preço Atual'}</div>
                    <div class="vehicle-stat-value">${displayValues.format(displayValues.current)}</div>
                </div>
                <div class="vehicle-stat-item">
                    <div class="vehicle-stat-label">${isBase100 ? 'Índice Mínimo' : 'Preço Mínimo'}</div>
                    <div class="vehicle-stat-value">${displayValues.format(displayValues.min)}</div>
                </div>
                <div class="vehicle-stat-item">
                    <div class="vehicle-stat-label">${isBase100 ? 'Índice Máximo' : 'Preço Máximo'}</div>
                    <div class="vehicle-stat-value">${displayValues.format(displayValues.max)}</div>
                </div>
                <div class="vehicle-stat-item">
                    <div class="vehicle-stat-label">Variação</div>
                    <div class="vehicle-stat-value ${priceChange > 0 ? 'positive' : priceChange < 0 ? 'negative' : ''}">
                        ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}%
                    </div>
                </div>
                <div class="vehicle-stat-item">
                    <div class="vehicle-stat-label">IPCA (${periodLabel})</div>
                    <div class="vehicle-stat-value ${indicators.ipca !== null ? 'neutral' : ''}">
                        ${indicators.ipca !== null ? (indicators.ipca > 0 ? '+' : '') + indicators.ipca.toFixed(2) + '%' : 'N/A'}
                    </div>
                </div>
                <div class="vehicle-stat-item">
                    <div class="vehicle-stat-label">CDI (${periodLabel})</div>
                    <div class="vehicle-stat-value ${indicators.cdi !== null ? 'neutral' : ''}">
                        ${indicators.cdi !== null ? (indicators.cdi > 0 ? '+' : '') + indicators.cdi.toFixed(2) + '%' : 'N/A'}
                    </div>
                </div>
            </div>

            ${renderDepreciationSection(vehicle, depreciationMetrics, indicators, yearlyBreakdown)}
        `;

        container.appendChild(card);
    }
}

/**
 * Animate number counter for statistics
 */
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }

        if (element.id === 'priceChange') {
            const percent = current.toFixed(2);
            element.textContent = `${percent > 0 ? '+' : ''}${percent}%`;
        } else {
            element.textContent = formatBRL(current);
        }
    }, 16);
}

/**
 * Calculate and display statistics with smooth animations
 */
function updateStatistics(data) {
    if (!data || data.length === 0) return;

    const prices = data.map(d => d.price);
    const currentPrice = prices[prices.length - 1];
    const firstPrice = prices[0];
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    // Calculate price change (percentage and absolute)
    const priceChange = currentPrice - firstPrice;
    const priceChangePercent = ((priceChange / firstPrice) * 100);

    // Animate the statistics
    const currentPriceEl = document.getElementById('currentPrice');
    const minPriceEl = document.getElementById('minPrice');
    const maxPriceEl = document.getElementById('maxPrice');
    const priceChangeEl = document.getElementById('priceChange');

    // Add stagger animation to stat cards
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.animation = 'none';
        setTimeout(() => {
            card.style.animation = `slideInUp 0.5s ease-out ${index * 0.1}s both`;
        }, 10);
    });

    // Animate numbers
    setTimeout(() => {
        animateValue(currentPriceEl, 0, currentPrice, 1000);
        animateValue(minPriceEl, 0, minPrice, 1000);
        animateValue(maxPriceEl, 0, maxPrice, 1000);
        animateValue(priceChangeEl, 0, priceChangePercent, 1000);
    }, 200);

    // Add color based on change direction
    if (priceChange > 0) {
        priceChangeEl.className = 'mb-0 text-success';
    } else if (priceChange < 0) {
        priceChangeEl.className = 'mb-0 text-danger';
    } else {
        priceChangeEl.className = 'mb-0 text-secondary';
    }
}

/**
 * Load default vehicle from API
 */
async function loadDefaultVehicle() {
    try {
        const response = await fetch('/api/default-car', {
            credentials: 'same-origin'
        });
        const defaultCar = await response.json();

        if (!defaultCar.brand_id || !defaultCar.model_id || !defaultCar.year_id) {
            return; // No default car available
        }

        // Select the brand
        const brandSelect = document.getElementById('brandSelect');
        brandSelect.value = defaultCar.brand_id;

        // Load and select the model
        await loadModels(defaultCar.brand_id);
        const modelSelect = document.getElementById('modelSelect');
        modelSelect.value = defaultCar.model_id;

        // Load and select the year
        await loadYears(defaultCar.model_id);
        const yearSelect = document.getElementById('yearSelect');
        yearSelect.value = defaultCar.year_id;

        // Load months for this vehicle
        await loadMonths(defaultCar.year_id);

        // Add the vehicle to comparison automatically
        const brandName = brandSelect.options[brandSelect.selectedIndex].text;
        const modelName = modelSelect.options[modelSelect.selectedIndex].text;
        const yearDesc = yearSelect.options[yearSelect.selectedIndex].text;

        const vehicle = {
            id: defaultCar.year_id,
            brand: brandName,
            model: modelName,
            year: yearDesc,
            color: VEHICLE_COLORS[0]
        };

        selectedVehicles.push(vehicle);
        updateVehiclesUI();
        updateButtonsState();

        // Load and display the chart for the default vehicle
        await updateComparisonChart();

    } catch (error) {
        console.error('Error loading default vehicle:', error);
        // Don't show error to user - just continue without default
    }
}

/**
 * Initialize app with default selections
 */
async function initializeApp() {
    try {
        // Load all brands
        await loadBrands();

        // Load all months (will be updated when vehicle is selected)
        await loadMonths();

        // Load default vehicle and chart
        await loadDefaultVehicle();

        // Hide loading spinner
        hideLoading();

    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Erro ao inicializar aplicação');
    }
}

/**
 * Initialize event listeners
 */
function initEventListeners() {
    // Brand selection change - load all vehicle options for bidirectional filtering
    document.getElementById('brandSelect').addEventListener('change', async (e) => {
        const brandId = e.target.value;
        if (brandId) {
            // Load all models and years for this brand at once
            await loadVehicleOptions(brandId);
            updateButtonsState();
        } else {
            // Reset vehicle options and dropdowns
            vehicleOptions = null;
            document.getElementById('modelSelect').innerHTML = '<option value="">Selecione uma marca</option>';
            document.getElementById('modelSelect').disabled = true;
            document.getElementById('yearSelect').innerHTML = '<option value="">Selecione um modelo</option>';
            document.getElementById('yearSelect').disabled = true;
            updateButtonsState();
        }
    });

    // Model selection change - filter years based on selected model
    document.getElementById('modelSelect').addEventListener('change', async (e) => {
        const modelId = e.target.value;
        const yearSelect = document.getElementById('yearSelect');

        if (modelId) {
            // Filter years to show only those available for this model
            filterYearsByModel(modelId);

            // If both model and year are selected, load months for that specific vehicle
            if (yearSelect.value) {
                const yearDesc = yearSelect.value;
                const modelIdStr = String(modelId);

                // Look up the ModelYear ID
                if (vehicleOptions && vehicleOptions.model_year_lookup) {
                    const yearId = vehicleOptions.model_year_lookup[modelIdStr]?.[yearDesc];
                    if (yearId) {
                        await loadMonths(yearId);
                    }
                }
            }
        } else {
            // Model cleared - restore all years
            if (vehicleOptions) {
                populateYearDropdown(vehicleOptions.year_descriptions);
            }
        }
        updateButtonsState();
    });

    // Year selection change - filter models based on selected year
    document.getElementById('yearSelect').addEventListener('change', async (e) => {
        const yearDesc = e.target.value;
        const modelSelect = document.getElementById('modelSelect');

        if (yearDesc) {
            // Filter models to show only those available for this year
            filterModelsByYear(yearDesc);

            // If both model and year are selected, load months for that specific vehicle
            if (modelSelect.value) {
                const modelId = modelSelect.value;
                const modelIdStr = String(modelId);

                // Look up the ModelYear ID
                if (vehicleOptions && vehicleOptions.model_year_lookup) {
                    const yearId = vehicleOptions.model_year_lookup[modelIdStr]?.[yearDesc];
                    if (yearId) {
                        await loadMonths(yearId);
                    }
                }
            }
        } else {
            // Year cleared - restore all models
            if (vehicleOptions) {
                populateModelDropdown(vehicleOptions.models);
            }
        }
        updateButtonsState();
    });

    // Add vehicle button click
    document.getElementById('addVehicle').addEventListener('click', addVehicle);

    // Update button click
    document.getElementById('updateChart').addEventListener('click', updateChart);

    // Chart type change - re-render chart with new type
    document.getElementById('chartType').addEventListener('change', () => {
        if (selectedVehicles.length > 0) {
            renderComparisonChart();
            updateComparisonStatistics();
        }
    });

    // Enter key in selects triggers update
    ['brandSelect', 'modelSelect', 'yearSelect', 'startMonth', 'endMonth'].forEach(id => {
        document.getElementById(id).addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !document.getElementById('updateChart').disabled) {
                updateChart();
            }
        });
    });
}

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('FIPE Price Tracker - Multi-vehicle comparison initialized');

    // Set up event listeners
    initEventListeners();

    // Initialize the app
    initializeApp();
});
