# Compile production and development dependencies
compile-requirements:
	pip-compile --upgrade requirements/dev.in -o requirements/dev.txt
	pip-compile --upgrade requirements/prod.in -o requirements/prod.txt

# Install dependencies
install-prod:
	pip install -r requirements/prod.txt
install-dev:
	pip install -r requirements/dev.txt

# Clean up build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Run linter
lint:
	flake8 .

# Run code format
format:
	black .
	isort .

# Build docker image
build:
	sudo docker build -t ndi_record .

# Run docker container
run:
	sudo docker run -it --rm --gpus all --runtime=nvidia --network host --privileged \
	-v /var/run/dbus:/var/run/dbus \
	-v /run/avahi-daemon/socket:/run/avahi-daemon/socket \
	-v /home/geri/work/datasets/test/:/app/output/ \
	ndi_record