FROM node:20-alpine

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

WORKDIR /app

COPY package.json .npmrc* ./
RUN npm install --legacy-peer-deps && \
    rm -rf /app/node_modules/fork-ts-checker-webpack-plugin/node_modules/ajv-keywords \
           /app/node_modules/fork-ts-checker-webpack-plugin/node_modules/schema-utils

COPY . .
RUN npm run build

RUN npm install -g serve

CMD serve -s build -l ${PORT:-3000}
