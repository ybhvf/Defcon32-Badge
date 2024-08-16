.PHONY:clean micropython littlefs submodules

build/firmware.uf2: build micropython littlefs

clean:
	$(MAKE) -C micropython/ports/rp2 clean
	rm -f build/firmware.uf2

build:
	mkdir -p build

micropython:
	$(MAKE) -C micropython/mpy-cross
	$(MAKE) -C micropython/ports/rp2 \
		BOARD=RPI_PICO \
		USER_C_MODULES=$(CURDIR)/ulab/code/micropython.cmake \
		FROZEN_MANIFEST=$(CURDIR)/manifest.py

littlefs: micropython
	cd build && \
		../utils/dir2uf2/dir2uf2 --verbose \
			--fs-start 269090816 --fs-compact \
			--manifest ../littlefs.txt \
			--append-to ../micropython/ports/rp2/build-RPI_PICO/firmware.uf2 \
			../ziatv
	rm build/filesystem.bin build/filesystem.uf2
	mv build/firmware-filesystem.uf2 build/firmware.uf2

submodules:
	git submodule update --init --checkout
	$(MAKE) -C micropython/ports/rp2 submodules
