import { test } from "node:test";
import assert from "node:assert/strict";
import {
  getActiveAccount,
  loadAccountState,
  registerAccount,
  signOut,
  switchAccount,
  validateAccount,
} from "../src/profile/profileStore.js";

function storage() {
  const data = new Map();
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
    removeItem: (key) => data.delete(key),
  };
}

test("account validates name and email", () => {
  assert.ok(validateAccount({ display_name: "A", email: "bad" }).display_name);
  assert.ok(validateAccount({ display_name: "A", email: "bad" }).email);
  assert.deepEqual(
    validateAccount({
      display_name: "Олена Коваленко",
      email: "doctor@example.com",
    }),
    {},
  );
});

test("local accounts can register, sign out and switch", () => {
  const store = storage();
  assert.equal(getActiveAccount(store), null);
  assert.equal(
    registerAccount(store, {
      display_name: " Олена Коваленко ",
      email: " doctor@example.com ",
    }).ok,
    true,
  );
  assert.equal(getActiveAccount(store).display_name, "Олена Коваленко");
  assert.equal(signOut(store), true);
  assert.equal(getActiveAccount(store), null);
  assert.equal(
    registerAccount(store, {
      display_name: "Павло",
      email: "second@example.com",
    }).ok,
    true,
  );
  assert.equal(loadAccountState(store).accounts.length, 2);
  assert.equal(switchAccount(store, "doctor@example.com"), true);
  assert.equal(getActiveAccount(store).email, "doctor@example.com");
  assert.equal(switchAccount(store, "missing@example.com"), false);
});

test("duplicate and invalid accounts are rejected", () => {
  const store = storage();
  assert.equal(
    registerAccount(store, { display_name: "", email: "bad" }).ok,
    false,
  );
  assert.equal(
    registerAccount(store, {
      display_name: "Олена",
      email: "Doctor@example.com",
    }).ok,
    true,
  );
  assert.equal(
    registerAccount(store, {
      display_name: "Інша",
      email: "doctor@example.com",
    }).ok,
    false,
  );
  assert.equal(loadAccountState(store).accounts.length, 1);
});

test("previous local profile is migrated", () => {
  const store = storage();
  store.setItem(
    "renalcare.profile.v1",
    JSON.stringify({
      display_name: "Олена",
      email: "doctor@example.com",
    }),
  );
  assert.equal(getActiveAccount(store).display_name, "Олена");
  assert.equal(store.getItem("renalcare.profile.v1"), null);
});
