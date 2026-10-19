import { fireEvent, render, screen } from "@testing-library/react";

import { ThemeToggle } from "./ThemeToggle";

test("the button switches the page to dark and back", () => {
  render(<ThemeToggle />);

  fireEvent.click(screen.getByRole("button", { name: "Dark" }));
  expect(document.documentElement).toHaveClass("dark");

  fireEvent.click(screen.getByRole("button", { name: "Light" }));
  expect(document.documentElement).not.toHaveClass("dark");
});
