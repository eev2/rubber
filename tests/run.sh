#!/bin/sh
# really basic test driver
# copy the rubber source, and the test case data to a temporary
# directory, and run rubber on the file.

SOURCE_DIR="$(cd ..; pwd)"
tmpdir=tmp

set -e                          # Stop at first failure.

KEEP=false
VERBOSE=
while [ 1 -le $# ]; do
    case $1 in
        --rmtmp)
            rm -rf $tmpdir
            shift
            ;;
        -k)
            KEEP=true
            shift
            ;;
        -v|-vv|-vvv)
            VERBOSE="$VERBOSE $1"
            shift
            ;;
        *)
            break
    esac
done

echo "When a test fails, please remove the $tmpdir directory manually."

list0() {
    (cd "$1"; find -mindepth 1 -print0)
}

for main; do
    [ "$main" = 'run.sh' ] && continue
    [ "$main" = 'shared' ] && continue

    [ -d $main ] || {
        echo "$main must be a directory"
        exit 1
    }

    [ -e $main/disable ] && {
        echo "Skipping test $main"
        continue
    }

    echo "Test: $main"

    mkdir $tmpdir
    cp $main/* $tmpdir
    cp shared/* $tmpdir
    gzip -c shared/sample.eps > $tmpdir/compressed.eps.gz
    cd $tmpdir

    cp -a "$SOURCE_DIR/src" rubber

    cat > usrbinrubber.py <<EOF
import sys, rubber.cmdline
sys.exit (rubber.cmdline.Main () (sys.argv [1:]))
EOF

    cat >> rubber/version.py <<EOF
version = "unreleased"
moddir = "$SOURCE_DIR/data"
EOF

    rubber="python usrbinrubber.py $VERBOSE"

    if [ -e fragment ]; then
        # test brings their own code
        . ./fragment
    else
        # default test code:  try to build two times, clean up.
        if test -r document; then
            read doc < document
        else
            doc=doc
        fi
        if test -r arguments; then
            read arguments < arguments
        fi

        echo Running rubber $arguments $doc ...

        $rubber $arguments         $doc

        if $KEEP; then
            echo "Keeping ${tmpdir}."
            exit 1
        fi

        $rubber $arguments         $doc
        $rubber $arguments --clean $doc

        unset doc arguments
    fi

    rm -r rubber
    rm usrbinrubber.py
    rm compressed.eps.gz
    (list0 ../$main; list0 ../shared) | xargs -0 rm -r
    cd ..

    rmdir $tmpdir || {
        echo "Directory $tmpdir is not left clean:"
        ls $tmpdir
        exit 1
    }
done

echo OK
