# Compile production and development dependencies
compile-requirements:
	pip-compile --upgrade requirements/requirements.in -o requirements/requirements.txt

# Install dependencies
install:
	pip install -r requirements/requirements.txt

# Clean up build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Build docker image
# TODO: Install nvidia-docker, modify daemon and restart docker
build:
	sudo docker build -t ndi_record .

# Run docker container
run:
	sudo docker run -it --rm \
	--gpus all \
	--runtime=nvidia \
	--network host \
	-v /var/run/dbus:/var/run/dbus \
	-v /run/avahi-daemon/socket:/run/avahi-daemon/socket \
	-v /home/geri/work/datasets/test/:/app/output/ \
	ndi_record