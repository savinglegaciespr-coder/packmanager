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
    printf 'module.exports = class {};\n' > /app/node_modules/react-dev-utils/ForkTsCheckerWarningsWebpackPlugin.js && \
    mkdir -p /app/node_modules/ajv-keywords/node_modules && \
    ln -sfn /app/node_modules/schema-utils/node_modules/ajv \
            /app/node_modules/ajv-keywords/node_modules/ajv

COPY . .
RUN npm run build

RUN npm install -g serve@13

RUN printf '#!/bin/sh\nP=${PORT:-3000}\n[ "$P" = "null" ] && P=3000\nexec serve -s /app/build -l "$P"\n' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
