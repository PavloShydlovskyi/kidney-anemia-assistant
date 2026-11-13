import { test } from "node:test";
import assert from "node:assert/strict";
import { validateAuth } from "../src/profile/authValidation.js";
import { request } from "../src/api/httpClient.js";

test("registration requires a valid name, email and password", () => {
  const errors = validateAuth(
    { display_name: "A", email: "bad", password: "123" },
    true,
  );
  assert.deepEqual(Object.keys(errors), ["display_name", "email", "password"]);
  assert.deepEqual(
    validateAuth(
      {
        display_name: "Олена Коваленко",
        email: "olena@example.com",
        password: "strong-pass",
      },
      true,
    ),
    {},
  );
});

test("login does not require a name", () => {
  assert.deepEqual(
    validateAuth(
      { display_name: "", email: "olena@example.com", password: "strong-pass" },
      false,
    ),
    {},
  );
});

test("requests include the server session cookie", async () => {
  let options;
  await request("/api/auth/session", {}, async (_url, init) => {
    options = init;
    return { ok: true, status: 200, json: async () => ({ user: null }) };
  });
  assert.equal(options.credentials, "include");
  assert.equal(options.cache, "no-store");
});
