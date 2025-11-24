FROM nginx:stable-alpine

# Copy static site into nginx html dir
WORKDIR /usr/share/nginx/html
# When Cloud Build uses the repo root as the build context, the static
# assets live under `web/static`. Ensure we COPY from that path so Kaniko
# can find the files.
COPY web/static ./

# Replace default nginx config with one that listens on 8080 so Cloud Run
# health/startup checks on $PORT (8080) succeed.
COPY web/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
