import { escapeHtml, redditLink } from "./links";

test("a post opens its thread and a comment opens itself on Reddit", () => {
  expect(redditLink({ id: "t1", thread_id: "t1", kind: "post" })).toBe(
    "https://www.reddit.com/r/sailing/comments/t1/",
  );
  expect(redditLink({ id: "c9", thread_id: "t1", kind: "comment" })).toBe(
    "https://www.reddit.com/r/sailing/comments/t1/comment/c9/",
  );
});

test("text people wrote can't become markup in the hover card", () => {
  expect(escapeHtml(`<img src=x onerror="alert('hi')"> & more`)).toBe(
    "&lt;img src=x onerror=&quot;alert(&#39;hi&#39;)&quot;&gt; &amp; more",
  );
});
