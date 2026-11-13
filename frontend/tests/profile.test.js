import { test } from "node:test";
import assert from "node:assert/strict";
import {
  clearProfile,
  loadProfile,
  saveProfile,
  validateProfile,
} from "../src/profile/profileStore.js";

function storage() {
  const data = new Map();
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
    removeItem: (key) => data.delete(key),
  };
}

test("profile validates name and email", () => {
  assert.ok(validateProfile({ display_name: "A", email: "bad" }).display_name);
  assert.ok(validateProfile({ display_name: "A", email: "bad" }).email);
  assert.deepEqual(
    validateProfile({
      display_name: "Олена Коваленко",
      email: "doctor@example.com",
    }),
    {},
  );
});

test("profile can be saved, loaded and cleared locally", () => {
  const store = storage();
  const profile = {
    display_name: "  Олена Коваленко ",
    email: " doctor@example.com ",
  };
  assert.equal(saveProfile(store, profile).ok, true);
  assert.deepEqual(loadProfile(store), {
    display_name: "Олена Коваленко",
    email: "doctor@example.com",
  });
  assert.equal(clearProfile(store), true);
  assert.deepEqual(loadProfile(store), { display_name: "", email: "" });
});

test("invalid profile is not stored", () => {
  const store = storage();
  assert.equal(
    saveProfile(store, { display_name: "", email: "bad" }).ok,
    false,
  );
  assert.deepEqual(loadProfile(store), { display_name: "", email: "" });
});
