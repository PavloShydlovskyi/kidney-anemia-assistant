export const PROFILE_KEY = "renalcare.profile.v1";

export function validateProfile(profile) {
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

export function loadProfile(storage) {
  try {
    const data = JSON.parse(storage.getItem(PROFILE_KEY));
    if (
      typeof data?.display_name === "string" &&
      typeof data?.email === "string"
    ) {
      return { display_name: data.display_name, email: data.email };
    }
  } catch {
    // Storage may be unavailable or contain an older format.
  }
  return { display_name: "", email: "" };
}

export function saveProfile(storage, profile) {
  const data = {
    display_name: profile.display_name.trim(),
    email: profile.email.trim(),
  };
  const errors = validateProfile(data);
  if (Object.keys(errors).length) return { ok: false, errors };
  try {
    storage.setItem(PROFILE_KEY, JSON.stringify(data));
    return { ok: true, data };
  } catch {
    return { ok: false, message: "Не вдалося зберегти дані в цьому браузері." };
  }
}

export function clearProfile(storage) {
  try {
    storage.removeItem(PROFILE_KEY);
    return true;
  } catch {
    return false;
  }
}
