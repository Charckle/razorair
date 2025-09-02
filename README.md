# What
- A webapp for managing the HVAC system for a house

## generate password
- `docker image pull charckle/razorair:latest` or the image you wnt to use
- `docker run --rm -it charckle/strirazorairbog_web_manager:latest python generate_password.py`


## podman
- the container runs as the user 1000 inside, but because of the user ID mapping, it will be something else on the local machine
    - this is how you change the mountesd folders accordingly:
    - `podman unshare chown -R 1000:1000 ./data`