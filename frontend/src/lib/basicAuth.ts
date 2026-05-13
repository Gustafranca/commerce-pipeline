/** Build RFC 7617 Basic Authorization header (UTF-8 safe for typical dashboard passwords). */
export function basicAuthHeader(user: string, pass: string): string {
  const raw = `${user}:${pass}`;
  const bytes = new TextEncoder().encode(raw);
  let bin = "";
  bytes.forEach((b) => {
    bin += String.fromCharCode(b);
  });
  return `Basic ${btoa(bin)}`;
}
