FROM node:20-alpine

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Disable CRA's ESLint webpack plugin (ajv v6/v8 mismatch) and TS checker
ENV DISABLE_ESLINT_PLUGIN=true
ENV TSC_COMPILE_ON_ERROR=true

WORKDIR /app

COPY package.json .npmrc* ./
RUN npm install --legacy-peer-deps && \
    rm -rf /app/node_modules/fork-ts-checker-webpack-plugin/node_modules/ajv-keywords \
           /app/node_modules/fork-ts-checker-webpack-plugin/node_modules/schema-utils && \
    printf 'module.exports = class {};\n' > /app/node_modules/react-dev-utils/ForkTsCheckerWebpackPlugin.js && \
    printf 'module.exports = class {};\n' > /app/node_modules/react-dev-utils/ForkTsCheckerWarningsWebpackPlugin.js

COPY . .
RUN npm run build
RUN ls -la /app/build/ && echo "--- index.html check ---" && cat /app/build/index.html | head -3 || echo "NO index.html found"

RUN npm install -g serve@13

RUN printf '#!/bin/sh\nP=${PORT:-3000}\n[ "$P" = "null" ] && P=3000\nexec serve -s /app/build -l "$P"\n' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
