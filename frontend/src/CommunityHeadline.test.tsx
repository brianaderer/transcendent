import { render, screen } from "@testing-library/react";

import { CommunityHeadline } from "./CommunityHeadline";

test("names the community the app follows, linked to it on Reddit", () => {
  render(<CommunityHeadline />);

  const link = screen.getByRole("link", { name: "r/sailing" });
  expect(link).toHaveAttribute("href", "https://www.reddit.com/r/sailing/");
  expect(screen.getByText(/8 weeks of its posts/)).toBeInTheDocument();
});
