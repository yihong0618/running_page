FROM python:local AS data
ARG app
ARG nike_refresh_token
ARG secret_string
ARG client_id
ARG client_secret
ARG refresh_token
ARG keep_phone_number
ARG keep_password

WORKDIR /root/running_page
COPY . /root/running_page/
ARG DUMMY=unknown
RUN DUMMY=${DUMMY}; \
  echo $app ; \
  if [ "$app" = "NRC" ] ; then \
  python3 run_page/nike_sync.py ${nike_refresh_token}; \
  elif [ "$app" = "Garmin" ] ; then \
  python3 run_page/garmin_sync.py ${secret_string} ; \
  elif [ "$app" = "Garmin-CN" ] ; then \
  python3 run_page/garmin_sync.py ${secret_string} --is-cn ; \
  elif [ "$app" = "Strava" ] ; then \
  python3 run_page/strava_sync.py ${client_id} ${client_secret} ${refresh_token};\
  elif [ "$app" = "Nike_to_Strava" ] ; then \
  python3  run_page/nike_to_strava_sync.py ${nike_refresh_token} ${client_id} ${client_secret} ${refresh_token};\
  elif [ "$app" = "Keep" ] ; then \
  python3 run_page/keep_sync.py ${keep_phone_number} ${keep_password};\
  else \
  echo "Unknown app" ; \
  fi
RUN python3 run_page/gen_svg.py --from-db --title "harus running page" --type grid --athlete "haru" --output assets/grid.svg --min-distance 5.0 --special-color yellow --special-color2 red --special-distance 10 --special-distance2 20 --use-localtime \
  && python3 run_page/gen_svg.py --from-db --title "harus running page" --type github --athlete "haru" --special-distance 5 --special-distance2 10 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5 \
  && python3 run_page/gen_svg.py --from-db --type circular --use-localtime


FROM node:local AS frontend-build
WORKDIR /root/running_page
COPY --from=data /root/running_page /root/running_page
RUN pnpm run build

FROM nginx:alpine AS web
COPY --from=frontend-build /root/running_page/dist /usr/share/nginx/html/
COPY --from=frontend-build /root/running_page/assets /usr/share/nginx/html/assets
