FROM node:18-alpine as builder

WORKDIR /app
COPY ./package.json yarn.lock ./
RUN yarn install --frozen-lockfile
COPY . .
RUN npx prisma db push
RUN npx prisma generate
RUN yarn seed
RUN yarn build

FROM node:18-alpine as runner

WORKDIR /app
COPY --from=builder /app/package.json .
COPY --from=builder /app/yarn.lock .
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/ ./.next/
EXPOSE 3000

ENTRYPOINT ["yarn", "start"]