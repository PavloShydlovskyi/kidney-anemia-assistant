const ACCOUNTS_KEY = "renalcare.accounts.v1";
const LEGACY_PROFILE_KEY = "renalcare.profile.v1";

export function validateAccount(profile) {
  const errors = {};
  const name = profile.display_name.trim();
  const email = profile.email.trim();
  if (name.length < 2 || name.length > 80) {
    errors.display_name = "Введіть ім’я від 2 до 80 символів.";
  }
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = "Введіть коректну електронну пошту.";
  }
  return errors;
}

export function loadAccountState(storage) {
  try {
    const saved = storage.getItem(ACCOUNTS_KEY);
    if (saved !== null) {
      const data = JSON.parse(saved);
      const accounts = Array.isArray(data.accounts)
        ? data.accounts.filter(
            (item) =>
              typeof item?.id === "string" &&
              typeof item?.display_name === "string" &&
              typeof item?.email === "string",
          )
        : [];
      const activeId = accounts.some((item) => item.id === data.activeId)
        ? data.activeId
        : null;
      return { accounts, activeId };
    }
    const previous = JSON.parse(storage.getItem(LEGACY_PROFILE_KEY));
    if (previous && !Object.keys(validateAccount(previous)).length) {
      const account = {
        id: previous.email.trim().toLowerCase(),
        display_name: previous.display_name.trim(),
        email: previous.email.trim(),
      };
      const state = { accounts: [account], activeId: account.id };
      storage.setItem(ACCOUNTS_KEY, JSON.stringify(state));
      storage.removeItem(LEGACY_PROFILE_KEY);
      return state;
    }
  } catch {
    // Storage can be disabled or contain an older format.
  }
  return { accounts: [], activeId: null };
}

export function getActiveAccount(storage) {
  const state = loadAccountState(storage);
  return state.accounts.find((item) => item.id === state.activeId) ?? null;
}

export function registerAccount(storage, profile) {
  const data = {
    display_name: profile.display_name.trim(),
    email: profile.email.trim(),
  };
  const errors = validateAccount(data);
  if (Object.keys(errors).length) return { ok: false, errors };
  const state = loadAccountState(storage);
  const id = data.email.toLowerCase();
  if (state.accounts.some((item) => item.id === id)) {
    return {
      ok: false,
      errors: {
        email: "Цей профіль уже є на пристрої. Оберіть його зі списку.",
      },
    };
  }
  const account = { id, ...data };
  state.accounts.push(account);
  state.activeId = id;
  try {
    storage.setItem(ACCOUNTS_KEY, JSON.stringify(state));
    return { ok: true, account };
  } catch {
    return {
      ok: false,
      message: "Не вдалося зберегти профіль у цьому браузері.",
    };
  }
}

export function switchAccount(storage, id) {
  const state = loadAccountState(storage);
  if (!state.accounts.some((item) => item.id === id)) return false;
  state.activeId = id;
  try {
    storage.setItem(ACCOUNTS_KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

export function signOut(storage) {
  const state = loadAccountState(storage);
  state.activeId = null;
  try {
    storage.setItem(ACCOUNTS_KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}
