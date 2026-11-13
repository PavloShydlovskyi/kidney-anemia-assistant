import { createEgfrChart } from "../charts/egfrChart.js";
import { createHemoglobinChart } from "../charts/hemoglobinChart.js";
const el = (tag, className, text) => {
  const item = document.createElement(tag);
  item.className = className;
  if (text != null) item.textContent = text;
  return item;
};
const icon = (name) => {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  svg.classList.add("icon");
  svg.setAttribute("aria-hidden", "true");
  use.setAttribute("href", `#icon-${name}`);
  svg.append(use);
  return svg;
};
export function createHistoryView(region) {
  let charts = [];
  function reset() {
    charts.forEach((chart) => chart.destroy());
    charts = [];
    region.replaceChildren();
  }
  return {
    showLoading() {
      reset();
      const panel = el("div", "loading-panel");
      panel.append(el("span", "spinner"), el("p", "", "Завантажуємо історію…"));
      region.append(panel);
    },
    showError(message) {
      reset();
      region.append(el("div", "error-panel", message));
    },
    showHistory(data) {
      reset();
      if (!data.length) {
        const empty = el("div", "empty-state");
        const illustration = el("span", "empty-icon");
        illustration.append(icon("history"));
        empty.append(
          illustration,
          el("h2", "", "Обстежень поки немає"),
          el("p", "", "Для цього пацієнта ще не збережено оцінювань."),
        );
        region.append(empty);
        return;
      }
      const items = [...data]
        .filter(
          (item) =>
            item.created_at &&
            Number.isFinite(Number(item.egfr)) &&
            Number.isFinite(Number(item.hemoglobin_g_l)),
        )
        .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      region.append(
        el("p", "history-summary", `Знайдено оцінювань: ${data.length}`),
      );
      if (items.length) {
        const grid = el("div", "charts-grid");
        const canvases = [];
        for (const [title, subtitle] of [
          ["Динаміка ШКФ", "мл/хв/1,73 м²"],
          ["Динаміка гемоглобіну", "г/л"],
        ]) {
          const card = el("div", "chart-card");
          const wrap = el("div", "chart-wrap");
          const canvas = document.createElement("canvas");
          canvas.setAttribute("aria-label", title);
          canvas.setAttribute("role", "img");
          wrap.append(canvas);
          card.append(el("h3", "", title), el("p", "", subtitle), wrap);
          grid.append(card);
          canvases.push(canvas);
        }
        region.append(grid);
        charts = [
          createEgfrChart(canvases[0], items),
          createHemoglobinChart(canvases[1], items),
        ];
      }
      const list = el("div", "history-list");
      for (const item of [...data].sort(
        (a, b) => new Date(b.created_at ?? 0) - new Date(a.created_at ?? 0),
      )) {
        const card = el("article", "history-card");
        const info = el("div");
        info.append(
          el("strong", "", `Оцінювання #${item.id ?? "—"}`),
          el(
            "small",
            "",
            item.created_at
              ? new Date(item.created_at).toLocaleString("uk-UA")
              : "Дата невідома",
          ),
        );
        const badge = el(
          "span",
          "badge",
          `${item.gfr_category ?? "—"} · ${item.egfr_display ?? item.egfr ?? "—"}`,
        );
        card.append(info, badge);
        list.append(card);
      }
      region.append(list);
    },
  };
}
