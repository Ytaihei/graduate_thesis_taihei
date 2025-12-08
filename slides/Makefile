LATEXMK = latexmk
LATEXMK_OPT = -pdfdvi
BUILD_DIR = build
TARGET = main

all: $(BUILD_DIR)/$(TARGET).pdf

$(BUILD_DIR)/$(TARGET).pdf: $(TARGET).tex
	mkdir -p $(BUILD_DIR)
	$(LATEXMK) $(LATEXMK_OPT) -outdir=$(BUILD_DIR) $<

clean:
	rm -rf $(BUILD_DIR)

docker:
	docker run --rm -v $(CURDIR):/workdir texlive/texlive:latest sh -c 'cd /workdir && mkdir -p $(BUILD_DIR) && latexmk -pdfdvi -outdir=$(BUILD_DIR) $(TARGET).tex'

.PHONY: all clean docker
