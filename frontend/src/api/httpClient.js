import { API_BASE_URL } from "../config.js";
export class ApiError extends Error {
  constructor(message, status, details = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}
export async function request(path, options = {}, fetcher = fetch) {
  let response;
  try {
    response = await fetcher(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Не вдалося зв’язатися із сервером. Перевірте з’єднання та спробуйте ще раз.",
      0,
    );
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    /* empty or invalid JSON */
  }
  if (!response.ok)
    throw new ApiError(
      response.status === 401
        ? "Увійдіть в акаунт і спробуйте ще раз."
        : response.status === 409
          ? "Ця електронна пошта вже зареєстрована."
          : response.status === 404
            ? "Пацієнта не знайдено."
            : "Не вдалося отримати результат. Спробуйте ще раз.",
      response.status,
      Array.isArray(body?.detail) ? body.detail : [],
    );
  if (body === null && response.status === 204) return {};
  if (body === null)
    throw new ApiError("Сервер повернув порожню відповідь.", response.status);
  return body;
}
