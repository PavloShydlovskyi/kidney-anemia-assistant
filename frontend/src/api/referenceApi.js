import { request } from "./httpClient.js";
export const getReference = (fetcher) => request("/api/reference", {}, fetcher);
