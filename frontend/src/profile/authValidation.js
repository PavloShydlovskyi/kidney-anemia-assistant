export function validateAuth({ display_name, email, password }, registering) {
  const errors = {};
  if (
    registering &&
    (display_name.trim().length < 2 || display_name.trim().length > 80)
  )
    errors.display_name = "Введіть ім’я від 2 до 80 символів.";
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()))
    errors.email = "Введіть коректну електронну пошту.";
  if (password.length < 8) errors.password = "Введіть пароль від 8 символів.";
  return errors;
}
