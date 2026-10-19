import "@testing-library/jest-dom/vitest";

// jsdom doesn't scroll; the router restores the scroll position on every navigation.
window.scrollTo = () => {};
