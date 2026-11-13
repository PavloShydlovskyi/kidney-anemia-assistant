import { anemiaLabels, rbcLabels, sourceLabels } from "../i18n/labels.js";
const node = (tag, className, value) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (value !== undefined && value !== null) el.textContent = String(value);
  return el;
};
export function showResult(result) {
  const region = document.querySelector("#result-region");
  region.replaceChildren();
  const card = node("article", "result-card");
  const top = node("div", "result-top");
  top.append(
    node("h2", "", "Результат оцінювання"),
    node(
      "span",
      "result-date",
      result.created_at
        ? new Date(result.created_at).toLocaleDateString("uk-UA")
        : "Щойно",
    ),
  );
  card.append(top);
  const grid = node("div", "result-grid");
  for (const [label, value, sub] of [
    [
      "ШКФ",
      result.egfr_display ?? result.egfr ?? "—",
      `${result.gfr_category ?? "—"} · ${sourceLabels[result.egfr_source] ?? result.egfr_source ?? ""}`,
    ],
    [
      "Гемоглобін",
      result.hemoglobin_g_l == null ? "—" : `${result.hemoglobin_g_l} г/л`,
      anemiaLabels[result.anemia_grade] ?? result.anemia_grade ?? "—",
    ],
  ]) {
    const metric = node("div", "metric");
    metric.append(
      node("span", "metric-label", label),
      node("span", "metric-value", value),
      node("span", "metric-sub", sub),
    );
    grid.append(metric);
  }
  card.append(grid);
  if (result.rbc_status) {
    const section = node("div", "result-section");
    section.append(
      node("h3", "", "Еритроцити"),
      node("p", "", rbcLabels[result.rbc_status] ?? result.rbc_status),
    );
    card.append(section);
  }
  for (const [title, entries, className] of [
    ["Заходи для розгляду лікарем", result.measures, ""],
    ["Застереження", result.warnings, "warning-list"],
  ]) {
    if (!Array.isArray(entries) || !entries.length) continue;
    const section = node("div", "result-section");
    const list = node("ul", className);
    for (const entry of entries) list.append(node("li", "", entry));
    section.append(node("h3", "", title), list);
    card.append(section);
  }
  card.append(
    node(
      "p",
      "result-disclaimer",
      `Результат має інформаційний характер. Остаточне рішення приймає лікар.${result.guideline_version ? ` Версія рекомендацій: ${result.guideline_version}.` : ""}`,
    ),
  );
  region.append(card);
  region.scrollIntoView({ behavior: "smooth", block: "start" });
}
