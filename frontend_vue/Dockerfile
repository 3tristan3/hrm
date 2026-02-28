FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --include=dev --no-audit --no-fund

COPY . .

ARG VITE_API_BASE=
ARG VITE_FORM_URL=
ARG VITE_PREWARM_JOBS=true
ARG VITE_PREWARM_REGION_LIMIT=3
ENV VITE_API_BASE=${VITE_API_BASE}
ENV VITE_FORM_URL=${VITE_FORM_URL}
ENV VITE_PREWARM_JOBS=${VITE_PREWARM_JOBS}
ENV VITE_PREWARM_REGION_LIMIT=${VITE_PREWARM_REGION_LIMIT}
ENV NODE_OPTIONS=--max_old_space_size=2048

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
