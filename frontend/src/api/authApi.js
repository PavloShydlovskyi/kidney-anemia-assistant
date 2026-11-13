import { request } from "./httpClient.js";

export const getSession = () => request("/api/auth/session");
export const register = (data) =>
  request("/api/auth/register", { method: "POST", body: JSON.stringify(data) });
export const login = (data) =>
  request("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
export const logout = () => request("/api/auth/logout", { method: "POST" });
