# docker buildx create --name amd64-builder --use
docker buildx build --platform linux/amd64 -t tonylampada/jarbas:latest --push .
