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

// Multi-vehicle comparison state
let selectedVehicles = [];
const MAX_VEHICLES = 5;

// Color palette for different vehicles
const VEHICLE_COLORS = [
    '#2563eb', // Blue
    '#10b981', // Green
    '#f59e0b', // Amber
    '#ef4444', // Red
    '#8b5cf6'  // Purple
];

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

    const yearId = parseInt(yearSelect.value);
    const brandName = brandSelect.options[brandSelect.selectedIndex].text;
    const modelName = modelSelect.options[modelSelect.selectedIndex].text;
    const yearDesc = yearSelect.options[yearSelect.selectedIndex].text;

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
                    <div class="vehicle-chip-details">${vehicle.year}</div>
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
        const response = await fetch('/api/brands');
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
 * Load models for a specific brand
 */
async function loadModels(brandId) {
    try {
        const response = await fetch(`/api/models/${brandId}`);
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
        yearSelect.innerHTML = '<option value="">Selecione um modelo</option>';
        yearSelect.disabled = true;
        
        return models;
    } catch (error) {
        console.error('Error loading models:', error);
        showError('Erro ao carregar modelos');
    }
}

/**
 * Load years for a specific model
 */
async function loadYears(modelId) {
    try {
        const response = await fetch(`/api/years/${modelId}`);
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
        const response = await fetch(url);
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
                'Content-Type': 'application/json'
            },
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
    detailsP.textContent = selectedVehicles.map(v => `${v.brand} ${v.model} (${v.year})`).join(' • ');

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
    detailsP.textContent = `Ano/Combustível: ${carInfo.year}`;

    carInfoDiv.classList.remove('d-none');
}

/**
 * Render the Plotly chart with premium styling
 */
function renderChart(data) {
    // Prepare data for Plotly
    const dates = data.map(d => d.label);
    const prices = data.map(d => d.price);

    // Create gradient for the area under the line
    const trace = {
        x: dates,
        y: prices,
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
        hovertemplate: '<b>%{x}</b><br>' +
                      'Preço: R$ %{y:,.2f}<br>' +
                      '<extra></extra>'
    };

    // Premium layout configuration
    const layout = {
        autosize: true,
        title: {
            text: 'Evolução do Preço FIPE',
            font: {
                size: 24,
                family: 'Inter, -apple-system, sans-serif',
                weight: 700,
                color: '#111827'
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
                    color: '#1e3a8a'
                }
            },
            tickangle: -45,
            automargin: true,
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: '#1e3a8a'
            },
            gridcolor: '#dbeafe',
            gridwidth: 1,
            showline: true,
            linecolor: '#93c5fd',
            linewidth: 2
        },
        yaxis: {
            title: {
                text: 'Preço (R$)',
                font: {
                    size: 14,
                    family: 'Inter, -apple-system, sans-serif',
                    weight: 600,
                    color: '#1e3a8a'
                }
            },
            tickformat: ',.0f',
            automargin: true,
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: '#1e3a8a'
            },
            gridcolor: '#dbeafe',
            gridwidth: 1,
            showline: true,
            linecolor: '#93c5fd',
            linewidth: 2,
            zeroline: false
        },
        hovermode: 'x unified',
        plot_bgcolor: '#eff6ff',
        paper_bgcolor: 'white',
        margin: {
            l: 80,
            r: 40,
            t: 100,
            b: 120
        },
        hoverlabel: {
            bgcolor: '#111827',
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
 * Render comparison chart with multiple vehicle traces
 */
function renderComparisonChart() {
    // Create traces for each vehicle
    const traces = selectedVehicles.map((vehicle, index) => {
        if (!vehicle.data || vehicle.data.length === 0) return null;

        const dates = vehicle.data.map(d => d.label);
        const prices = vehicle.data.map(d => d.price);

        return {
            x: dates,
            y: prices,
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
            hovertemplate: '<b>%{fullData.name}</b><br>' +
                          '%{x}<br>' +
                          'Preço: R$ %{y:,.2f}<br>' +
                          '<extra></extra>'
        };
    }).filter(trace => trace !== null);

    // Premium layout configuration
    const layout = {
        autosize: true,
        title: {
            text: 'Comparação de Preços FIPE',
            font: {
                size: 24,
                family: 'Inter, -apple-system, sans-serif',
                weight: 700,
                color: '#111827'
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
                    color: '#1e3a8a'
                }
            },
            tickangle: -45,
            automargin: true,
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: '#1e3a8a'
            },
            gridcolor: '#dbeafe',
            gridwidth: 1,
            showline: true,
            linecolor: '#93c5fd',
            linewidth: 2
        },
        yaxis: {
            title: {
                text: 'Preço (R$)',
                font: {
                    size: 14,
                    family: 'Inter, -apple-system, sans-serif',
                    weight: 600,
                    color: '#1e3a8a'
                }
            },
            tickformat: ',.0f',
            automargin: true,
            tickfont: {
                size: 12,
                family: 'Inter, -apple-system, sans-serif',
                color: '#1e3a8a'
            },
            gridcolor: '#dbeafe',
            gridwidth: 1,
            showline: true,
            linecolor: '#93c5fd',
            linewidth: 2,
            zeroline: false
        },
        hovermode: 'x unified',
        plot_bgcolor: '#eff6ff',
        paper_bgcolor: 'white',
        margin: {
            l: 80,
            r: 40,
            t: 100,
            b: 120
        },
        hoverlabel: {
            bgcolor: '#111827',
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
                family: 'Inter, -apple-system, sans-serif'
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
 * Update statistics for comparison view
 */
function updateComparisonStatistics() {
    if (selectedVehicles.length === 0) return;

    // Collect all prices from all vehicles
    let allPrices = [];
    let latestPrices = [];
    let firstPrices = [];

    selectedVehicles.forEach(vehicle => {
        if (vehicle.data && vehicle.data.length > 0) {
            const prices = vehicle.data.map(d => d.price);
            allPrices = allPrices.concat(prices);
            latestPrices.push(prices[prices.length - 1]);
            firstPrices.push(prices[0]);
        }
    });

    if (allPrices.length === 0) return;

    // Calculate statistics
    const avgCurrentPrice = latestPrices.reduce((a, b) => a + b, 0) / latestPrices.length;
    const avgFirstPrice = firstPrices.reduce((a, b) => a + b, 0) / firstPrices.length;
    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const avgChange = ((avgCurrentPrice - avgFirstPrice) / avgFirstPrice) * 100;

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
        animateValue(currentPriceEl, 0, avgCurrentPrice, 1000);
        animateValue(minPriceEl, 0, minPrice, 1000);
        animateValue(maxPriceEl, 0, maxPrice, 1000);
        animateValue(priceChangeEl, 0, avgChange, 1000);
    }, 200);

    // Add color based on change direction
    if (avgChange > 0) {
        priceChangeEl.className = 'mb-0 text-success';
    } else if (avgChange < 0) {
        priceChangeEl.className = 'mb-0 text-danger';
    } else {
        priceChangeEl.className = 'mb-0 text-secondary';
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
        const response = await fetch('/api/default-car');
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
    // Brand selection change
    document.getElementById('brandSelect').addEventListener('change', async (e) => {
        const brandId = e.target.value;
        if (brandId) {
            await loadModels(brandId);
        } else {
            // Reset model and year dropdowns
            document.getElementById('modelSelect').innerHTML = '<option value="">Selecione uma marca</option>';
            document.getElementById('modelSelect').disabled = true;
            document.getElementById('yearSelect').innerHTML = '<option value="">Selecione um modelo</option>';
            document.getElementById('yearSelect').disabled = true;
        }
    });
    
    // Model selection change
    document.getElementById('modelSelect').addEventListener('change', async (e) => {
        const modelId = e.target.value;
        if (modelId) {
            await loadYears(modelId);
        } else {
            // Reset year dropdown
            document.getElementById('yearSelect').innerHTML = '<option value="">Selecione um modelo</option>';
            document.getElementById('yearSelect').disabled = true;
        }
    });
    
    // Year selection change - enable add button
    document.getElementById('yearSelect').addEventListener('change', async (e) => {
        const yearId = e.target.value;

        if (yearId) {
            // Load months available for this specific vehicle
            await loadMonths(parseInt(yearId));
            updateButtonsState();
        } else {
            // No year selected - disable add button
            updateButtonsState();
        }
    });

    // Add vehicle button click
    document.getElementById('addVehicle').addEventListener('click', addVehicle);

    // Update button click
    document.getElementById('updateChart').addEventListener('click', updateChart);
    
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
