import { existsSync } from "node:fs";

const required = [
  "dist/index.html",
  "dist/cards.html",
  "dist/authors.html",
  "dist/books.html",
  "dist/catalogue.html",
  "dist/research.html"
];

for (const path of required) {
  if (!existsSync(path)) throw new Error(`Missing required static entry: ${path}`);
}

console.log(`Biblioteca static build validated for ${process.env.PAGES_BASE || "/"}`);
