// The same rule the server applies. The browser shows `title` when it is not met.
export const usernameRule = {
  pattern: '[A-Za-z0-9][A-Za-z0-9._\\-]{2,29}',
  title: '3 to 30 letters, digits, dots, dashes or underscores',
  maxLength: 30,
  required: true,
}
