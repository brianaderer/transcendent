FROM node:22.12-slim

WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173
CMD ["npm", "run", "preview"]
