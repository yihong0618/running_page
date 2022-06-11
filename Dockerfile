FROM python:3.10.5-slim AS data
ARG app
ARG nike_refresh_token
ARG email 
ARG password
ARG client_id
ARG client_secret
ARG refresch_token
ARG YOUR_NAME
WORKDIR /root/running_page
COPY ./ /root/running_page
RUN pip3 install -i https://mirrors.aliyun.com/pypi/simple/ pip -U
RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip3 install -r requirements.txt
RUN if [ "$app" = "NRC" ] ; then \
       python3 scripts/nike_sync.py ${nike_refresh_token}; \
    elif ["$app" = "Garmin"] ; then \
         python3 scripts/gramin_sync.py ${email} ${password}; \
    elif ["$app" = "Garmin-CN"] ; then \
         python3 scripts/gramin_sync.py ${email} ${password}  --is-cn ; \
    elif ["$app" = "Strava"] ; then \
        python3 scripts/strava_sync.py ${client_id} ${client_secret} ${refresch_token};\
    elif ["$app" = "Nike_to_Strava"] ; then \
        python3  scripts/nike_to_strava_sync.py ${nike_refresh_token} ${client_id} ${client_secret} ${refresch_token};\
    else \
        echo "Unknown app" ; \
    fi
RUN python3 scripts/gen_svg.py --from-db --title "my running page" --type grid --athlete "$YOUR_NAME" --output assets/grid.svg --min-distance 10.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime
RUN python3 scripts/gen_svg.py --from-db --title "my running page" --type github --athlete "$YOUR_NAME" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5
RUN python3 scripts/gen_svg.py --from-db --type circular --use-localtime

FROM node:14  AS frontend
WORKDIR /root/
COPY --from=data /root/running_page /root/
RUN npm config set registry https://registry.npm.taobao.org
RUN yarn install
RUN yarn build

FROM nginx:alpine AS web
COPY --from=frontend /root/public /usr/share/nginx/html/
COPY --from=frontend /root/assets /usr/share/nginx/html/assets