import { escapeHtml } from "./html";

test("text people wrote can't become markup in the hover card", () => {
  expect(escapeHtml(`<img src=x onerror="alert('hi')"> & more`)).toBe(
    "&lt;img src=x onerror=&quot;alert(&#39;hi&#39;)&quot;&gt; &amp; more",
  );
});
