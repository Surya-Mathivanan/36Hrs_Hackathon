let trendChart, donutChart, monthlyBarChart, yearlyBarChart, weeklyBarChart;
let humanTrendChart, humanBreakdownChart, humanComparisonChart; // CORE FEATURE charts

function getDateRange(days) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    return {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0]
    };
}

function updateDashboard() {
    const days = parseInt(document.getElementById('dateRange').value);
    const dateRange = getDateRange(days);
    
    fetch(`/api/dashboard?start_date=${dateRange.start}&end_date=${dateRange.end}`)
        .then(response => response.json())
        .then(data => {
            console.log('📊 Dashboard data received:', data);
            updateKPIs(data.kpis);
            
            // Choose appropriate granularity based on time range
            let trendData, trendLabel;
            if (days <= 7) {
                // For 7 days or less, use daily data
                trendData = data.daily_trend || [];
                trendLabel = 'date';
            } else if (days <= 90) {
                // For 30-90 days, use weekly data
                trendData = data.weekly_trend || [];
                trendLabel = 'label';
            } else {
                // For 6 months, 1 year, use monthly data
                trendData = data.monthly_trend || [];
                trendLabel = 'month';
            }
            
            updateTrendChart(trendData, trendLabel, days);
            updateMonthlyBarChart(data.monthly_trend || []);
            updateYearlyBarChart(data.yearly_comparison || []);
            updateWeeklyBarChart(data.weekly_comparison || []);
            updateDonutChart(data.source_breakdown || []);
            
            // CORE FEATURE: Update human emissions KPIs only
            console.log('🔍 Checking human_emissions data:', data.human_emissions);
            if (data.human_emissions) {
                console.log('✅ Human emissions data found, updating KPIs...');
                updateHumanKPIs(data.human_emissions);
            } else {
                console.warn('⚠️ No human_emissions data in response!');
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

function updateKPIs(kpis) {
    if (!kpis) return;

    const totalEl = document.getElementById('totalEmissions');
    const changeEl = document.getElementById('percentChange');
    const biggestSourceEl = document.getElementById('biggestSource');
    const biggestSourcePercentEl = document.getElementById('biggestSourcePercent');
    const energyEl = document.getElementById('energySaved');

    const totalEmissions = Number(kpis.total_emissions ?? 0);
    totalEl.textContent = totalEmissions.toFixed(2);

    const changeRaw = Number(kpis.percent_change ?? 0);
    const direction = changeRaw >= 0 ? '↑' : '↓';
    const changeFormatted = Math.abs(changeRaw).toFixed(1);
    changeEl.textContent = `${direction} ${changeFormatted}%`;
    changeEl.style.color = changeRaw > 0 ? '#ff4757' : (changeRaw < 0 ? '#00d4aa' : '#e4e6eb');

    const source = kpis.biggest_source || 'N/A';
    const formattedSource = source
        .toString()
        .replace('_', ' ')
        .replace(/^./, c => c.toUpperCase());
    biggestSourceEl.textContent = formattedSource;

    const biggestSourcePercent = Number(kpis.biggest_source_percent ?? 0).toFixed(1);
    biggestSourcePercentEl.textContent = `${biggestSourcePercent}% of total`;

    energyEl.textContent = Number(kpis.energy_saved ?? 0).toLocaleString();
}

function updateTrendChart(trendData, labelKey, days) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    // Format labels based on data type
    let labels = trendData.map(d => {
        const rawLabel = d[labelKey];
        if (labelKey === 'date') {
            // Format date as MMM DD for daily data
            const date = new Date(rawLabel);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } else if (labelKey === 'label') {
            // Format week labels (e.g., "2025-W24" -> "Week 24")
            const weekNum = rawLabel.split('-W')[1];
            return `Week ${weekNum}`;
        } else {
            // Monthly labels (e.g., "2025-06" -> "Jun 2025")
            const [year, month] = rawLabel.split('-');
            const date = new Date(year, month - 1);
            return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        }
    });
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Emissions (Tonnes CO₂e)',
                data: trendData.map(d => d.emissions),
                borderColor: '#00d4aa',
                backgroundColor: 'rgba(0, 212, 170, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: days <= 7 ? 5 : (days <= 90 ? 4 : 3),
                pointBackgroundColor: '#00d4aa'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#e4e6eb'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                },
                x: {
                    ticks: {
                        color: '#b0b3b8',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#2d3748'
                    }
                }
            }
        }
    });
}

function updateDonutChart(sourceData) {
    const ctx = document.getElementById('donutChart').getContext('2d');
    
    if (donutChart) {
        donutChart.destroy();
    }
    
    const colors = ['#00d4aa', '#0099ff', '#ffa502', '#ff4757'];
    
    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sourceData.map(d => d.source.charAt(0).toUpperCase() + d.source.slice(1).replace('_', ' ')),
            datasets: [{
                data: sourceData.map(d => d.emissions),
                backgroundColor: colors,
                borderColor: '#242b3d',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e4e6eb',
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value.toFixed(2)} tonnes (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function updateMonthlyBarChart(monthlyData) {
    const canvas = document.getElementById('monthlyBarChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (monthlyBarChart) {
        monthlyBarChart.destroy();
    }

    const labels = monthlyData.map(d => d.month);
    const values = monthlyData.map(d => d.emissions);

    monthlyBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Monthly Emissions (Tonnes CO₂e)',
                    data: values,
                    backgroundColor: 'rgba(0, 212, 170, 0.7)',
                    borderColor: '#00d4aa',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#e4e6eb'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                },
                x: {
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                }
            }
        }
    });
}

function updateYearlyBarChart(yearlyData) {
    const canvas = document.getElementById('yearlyBarChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (yearlyBarChart) {
        yearlyBarChart.destroy();
    }

    const labels = yearlyData.map(d => d.year.toString());
    const values = yearlyData.map(d => d.emissions);

    yearlyBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Yearly Emissions (Tonnes CO₂e)',
                    data: values,
                    backgroundColor: 'rgba(0, 153, 255, 0.7)',
                    borderColor: '#0099ff',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#e4e6eb'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                },
                x: {
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                }
            }
        }
    });
}

function updateWeeklyBarChart(weeklyData) {
    const canvas = document.getElementById('weeklyBarChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (weeklyBarChart) {
        weeklyBarChart.destroy();
    }

    const labels = weeklyData.map(d => d.label);
    const values = weeklyData.map(d => d.emissions);

    weeklyBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Weekly Emissions (Tonnes CO₂e)',
                    data: values,
                    backgroundColor: 'rgba(255, 165, 2, 0.7)',
                    borderColor: '#ffa502',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#e4e6eb'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                },
                x: {
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                }
            }
        }
    });
}

// CORE FEATURE: Human Emissions Chart Functions
function updateHumanKPIs(humanData) {
    if (!humanData) {
        console.log('⚠️ No human emissions data received');
        return;
    }

    console.log('✅ Updating human KPIs with data:', humanData);
    
    document.getElementById('humanTotalCount').textContent = humanData.avg_total_count || 0;
    document.getElementById('humanStudentCount').textContent = humanData.avg_student_count || 0;
    document.getElementById('humanStaffCount').textContent = humanData.avg_staff_count || 0;
    
    const emissions = (humanData.total_emissions || 0).toFixed(2);
    console.log('Setting humanTotalEmissions to:', emissions);
    document.getElementById('humanTotalEmissions').textContent = emissions;
}

// Update cumulative statistics (all-time totals)
function updateCumulativeStats() {
    fetch('/api/human_cumulative_stats')
        .then(response => response.json())
        .then(data => {
            console.log('📊 Cumulative stats:', data);
            
            if (data.total_emissions !== undefined) {
                document.getElementById('cumulativeTotalEmissions').textContent = data.total_emissions.toFixed(2);
            }
            if (data.total_records !== undefined) {
                document.getElementById('cumulativeDays').textContent = data.total_records;
            }
            if (data.average_population !== undefined) {
                document.getElementById('cumulativeAvgPopulation').textContent = data.average_population;
            }
            if (data.average_students !== undefined) {
                document.getElementById('cumulativeAvgStudents').textContent = data.average_students;
            }
            if (data.average_staff !== undefined) {
                document.getElementById('cumulativeAvgStaff').textContent = data.average_staff;
            }
        })
        .catch(error => {
            console.error('Error fetching cumulative stats:', error);
        });
}

function updateHumanTrendChart(humanData, days) {
    const canvas = document.getElementById('humanTrendChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (humanTrendChart) {
        humanTrendChart.destroy();
    }

    // Choose appropriate granularity based on time range
    let trendData, labelKey;
    if (days <= 7) {
        trendData = humanData.daily_trend || [];
        labelKey = 'date';
    } else if (days <= 90) {
        trendData = humanData.weekly_trend || [];
        labelKey = 'label';
    } else {
        trendData = humanData.monthly_trend || [];
        labelKey = 'month';
    }

    // Format labels
    let labels = trendData.map(d => {
        const rawLabel = d[labelKey];
        if (labelKey === 'date') {
            const date = new Date(rawLabel);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } else if (labelKey === 'label') {
            const weekNum = rawLabel.split('-W')[1];
            return `Week ${weekNum}`;
        } else {
            const [year, month] = rawLabel.split('-');
            const date = new Date(year, month - 1);
            return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        }
    });

    humanTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Human CO₂ Emissions (Tonnes)',
                data: trendData.map(d => d.emissions),
                borderColor: '#00d4aa',
                backgroundColor: 'rgba(0, 212, 170, 0.2)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointBackgroundColor: '#00d4aa',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#e4e6eb'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                },
                x: {
                    ticks: {
                        color: '#b0b3b8',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#2d3748'
                    }
                }
            }
        }
    });
}

function updateHumanBreakdownChart(humanData) {
    const canvas = document.getElementById('humanBreakdownChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (humanBreakdownChart) {
        humanBreakdownChart.destroy();
    }

    const avgStudents = humanData.avg_student_count || 0;
    const avgStaff = humanData.avg_staff_count || 0;

    humanBreakdownChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Students', 'Staff'],
            datasets: [{
                data: [avgStudents, avgStaff],
                backgroundColor: ['#00d4aa', '#0099ff'],
                borderColor: '#242b3d',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e4e6eb',
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value.toLocaleString()} people (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function updateHumanComparisonChart(humanData, days) {
    const canvas = document.getElementById('humanComparisonChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (humanComparisonChart) {
        humanComparisonChart.destroy();
    }

    // Use population_data for detailed comparison
    const popData = humanData.population_data || [];
    
    // Limit data points for readability
    const maxPoints = 15;
    const step = Math.max(1, Math.floor(popData.length / maxPoints));
    const sampledData = popData.filter((_, index) => index % step === 0);

    const labels = sampledData.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    humanComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Students',
                    data: sampledData.map(d => d.students),
                    backgroundColor: 'rgba(0, 212, 170, 0.7)',
                    borderColor: '#00d4aa',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Staff',
                    data: sampledData.map(d => d.staff),
                    backgroundColor: 'rgba(0, 153, 255, 0.7)',
                    borderColor: '#0099ff',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'CO₂ Emissions',
                    data: sampledData.map(d => d.emissions),
                    type: 'line',
                    borderColor: '#ffa502',
                    backgroundColor: 'rgba(255, 165, 2, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    yAxisID: 'y1',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#e4e6eb'
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Population Count',
                        color: '#b0b3b8'
                    },
                    ticks: {
                        color: '#b0b3b8'
                    },
                    grid: {
                        color: '#2d3748'
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'CO₂ Emissions (Tonnes)',
                        color: '#ffa502'
                    },
                    ticks: {
                        color: '#ffa502'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    ticks: {
                        color: '#b0b3b8',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#2d3748'
                    }
                }
            }
        }
    });
}

function loadRecommendations() {
    fetch('/api/recommendations')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('recommendationsContainer');
            container.innerHTML = '';
            
            data.recommendations.forEach(rec => {
                const card = document.createElement('div');
                card.className = `recommendation-card priority-${rec.priority.toLowerCase()}`;
                card.innerHTML = `
                    <h4>${rec.title}</h4>
                    <p>${rec.description}</p>
                    <span class="priority-badge priority-${rec.priority.toLowerCase()}">
                        ${rec.priority} Priority
                    </span>
                `;
                container.appendChild(card);
            });
        })
        .catch(error => {
            console.error('Error fetching recommendations:', error);
            document.getElementById('recommendationsContainer').innerHTML = 
                '<p class="loading">Error loading recommendations</p>';
        });
}

document.addEventListener('DOMContentLoaded', function() {
    updateDashboard();
    loadRecommendations();
    updateCumulativeStats();  // Load all-time cumulative statistics
});
