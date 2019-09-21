#!/bin/bash
set -euxo pipefail

VERSION="387_base"
LIB_DIR="kent-${VERSION}/src/lib/"
INC_DIR="kent-${VERSION}/src/inc/"
HTS_DIR="kent-${VERSION}/src/htslib/"

if [ ! -f "v${VERSION}.tar.gz" ]; then
	wget "https://github.com/ucscGenomeBrowser/kent/archive/v${VERSION}.tar.gz"
fi

tar -xzvf "v${VERSION}.tar.gz" ${LIB_DIR} --strip-components=2 && mv lib src
tar -xzvf "v${VERSION}.tar.gz" ${INC_DIR} --strip-components=2 && mv inc include
tar -xzvf "v${VERSION}.tar.gz" ${HTS_DIR} --strip-components=2

patch src/bbiRead.c < bbiRead.c.diff
patch src/bigBed.c < bigBed.c.diff
patch src/makefile < makefile.diff
patch htslib/Makefile < htslib_makefile.diff
patch include/bbiFile.h < bbiFile.h.diff
