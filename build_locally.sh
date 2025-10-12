USERNAME=charckle
VERSION=$(cat VERSION)
IMAGE=razorair

docker build -f Dockerfile-alpine -t $USERNAME/$IMAGE:$VERSION-alpine .
