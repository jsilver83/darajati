HTML := feasibility-study.html  \
        charter.html               \
        capabilities.html          \
        srs.html                   \
        design.html                \
        approvals.html             \
        user-manual.html           \
        index.html

PDF :=  feasibility-study.pdf      \
        charter.pdf                \
        capabilities.pdf           \
        srs.pdf                    \
        design.pdf                 \
        approvals.pdf              \
        user-manual.pdf

all: html pdf

html: $(HTML)
pdf: $(PDF)

COMMON_OPTS := -a toc=left -a sectnums -a icons=font -a frame=topbot -a grid=rows -a source-highlighter=pygments -a pygments-style=autumn

###########################################################################
# list images included in a PDF document to convert them from svg to png.
# Example:
# srs.pdf srs.html: images/context.png
###########################################################################

%.html: %.adoc
	asciidoctor $(COMMON_OPTS) -n -a data-uri -d book $<

%.pdf: %.adoc itc-theme.yml
	asciidoctor-pdf $(COMMON_OPTS) -a pdf-stylesdir=. -a pdf-style=itc -d article $<

# not used currently
%.xml: %.adoc
	asciidoctor -b docbook -d article -a data-uri! $<

# approvals: no toc, tables without lines
approvals.pdf: approvals.adoc itc-theme.yml
	asciidoctor-pdf -a sectnums -a icons=font -a frame=none -a grid=none -a pdf-stylesdir=. -a pdf-style=itc -d article $<

# convert SVG to PNG for PDFs. requires the librsvg2-bin package
images/%.png: images/%.svg
	rsvg-convert $< > $@

clean:
	rm -f $(HTML) $(PDF)

.PHONY: all clean html pdf
