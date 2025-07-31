FROM node:18
WORKDIR /root/running_page
COPY ./package.json /root/running_page/package.json
COPY ./pnpm-lock.yaml /root/running_page/pnpm-lock.yaml
RUN npm config set registry https://registry.npmmirror.com \
  && corepack enable \
  && COREPACK_NPM_REGISTRY=https://registry.npmmirror.com pnpm install
