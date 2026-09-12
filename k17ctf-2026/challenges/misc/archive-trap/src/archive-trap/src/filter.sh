#!/bin/sh
for arg in "$@"; do
    case "$arg" in
        -exec)
            echo "You don't have permission for that" >&2
            exit 1
            ;;
    esac
done
exec find "$@"
 