import Chart from "chart.js/auto";
export function createEgfrChart(canvas, items) {
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: items.map((item) =>
        new Date(item.created_at).toLocaleDateString("uk-UA"),
      ),
      datasets: [
        {
          label: "ШКФ, мл/хв/1,73 м²",
          data: items.map((item) => item.egfr),
          borderColor: "#91b96d",
          backgroundColor: "rgba(145,185,109,.13)",
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: "#91b96d",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, max: 120, grid: { color: "#edf1e9" } },
      },
    },
  });
}
