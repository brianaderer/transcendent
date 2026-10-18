FROM node:22.12-slim

WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173
# vite preview doesn't handle Docker's stop signal; exit 0 on it so Ctrl+C reads as a clean stop.
CMD ["sh", "-c", "trap 'exit 0' TERM INT; npm run preview & wait"]
