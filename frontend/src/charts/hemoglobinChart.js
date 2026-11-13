import Chart from "chart.js/auto";
export function createHemoglobinChart(canvas, items) {
  const color = getComputedStyle(document.documentElement)
    .getPropertyValue("--color-ink")
    .trim();
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: items.map((item) =>
        new Date(item.created_at).toLocaleDateString("uk-UA"),
      ),
      datasets: [
        {
          label: "Гемоглобін, г/л",
          data: items.map((item) => item.hemoglobin_g_l),
          borderColor: color,
          fill: false,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: color,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, border: { display: false } },
        y: {
          beginAtZero: true,
          grid: { display: false },
          border: { display: false },
        },
      },
    },
  });
}
