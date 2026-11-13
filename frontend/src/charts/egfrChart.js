import Chart from "chart.js/auto";
export function createEgfrChart(canvas, items) {
  const color = getComputedStyle(document.documentElement)
    .getPropertyValue("--color-accent-ink")
    .trim();
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
          max: 120,
          grid: { display: false },
          border: { display: false },
        },
      },
    },
  });
}
