FROM nginx:stable-alpine

# Copy static site into nginx html dir
WORKDIR /usr/share/nginx/html
# When Cloud Build uses the repo root as the build context, the static
# assets live under `web/static`. Ensure we COPY from that path so Kaniko
# can find the files.
COPY web/static ./

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
